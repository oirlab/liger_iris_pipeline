from ..stpipe.base_step import LigerIRISStep
from .. import datamodels
from ..utils.parallelization_utils import numba_thread_scope
from ..utils.subarray import get_subarray_model
from ..calibrations import SaturationSelector

import numpy as np
from numba import njit, prange
import logging

logger = logging.getLogger(__name__)

SATURATED_FLAG_uint8 =  np.uint8(datamodels.dqflags.DQ_FLAGS["SATURATED"])
DO_NOT_USE_FLAG_uint8 = np.uint8(datamodels.dqflags.DQ_FLAGS["DO_NOT_USE"])


__all__ = ["SaturationCheckStep"]


class SaturationCheckStep(LigerIRISStep):
    """
    Flag saturated pixels in ramps.

    Parameters
    ----------
    input : RampModel
        Input ramp model to check for saturation.
    max_cores : int, optional
        Maximum number of CPU cores to use.
        Default is 1.

    Calibrations
    ------------
    saturation : `SaturationModel` - Selector: `SaturationSelector`

    Returns
    -------
    `ProcessedRampModel`
        The input ramp model with updated ``dq_raw`` array where saturated pixels are flagged as ``SATURATED`` and ``DO_NOT_USE``.
    """

    spec = """
        suffix = string(default='')
    """

    calibrations = {
        'saturation' : {
            'selector' : SaturationSelector,
            'selector_kwargs' : {}
        }
    }
    class_alias = "sat_check"

    def process(self, input):

        # Open the input data model
        input_model = self.open_model(input)

        # Get output model
        if not isinstance(input_model, datamodels.ProcessedRampModel):
            output_model = datamodels.ProcessedRampModel.from_datamodels(
                input_model,
                include_data=True
            )
        else:
            output_model = input_model

        # Get the name of the dark reference file to use
        sat_ref, _ = self.get_calibration(output_model, "saturation")
        logger.info(f"Using saturation reference {sat_ref}")

        with self.open_model(sat_ref) as saturation_model:

            # Get subarray model if needed
            saturation_model_subarray = get_subarray_model(output_model, saturation_model)

            # Do the saturation check
            check_saturation(
                output_model.data, output_model.dq_raw, output_model.dq,
                saturation_model_subarray.sat_thresh, saturation_model_subarray.dq,
                max_cores=self.max_cores
            )

        # Return the corrected data model
        return output_model

def check_saturation(
    input_data : np.ndarray, input_dq_raw : np.ndarray, input_dq : np.ndarray,
    sat_thresh : np.ndarray, sat_dq : np.ndarray,
    max_cores : int = 1
):
    """
    Flag saturated pixels in ramps.

    Parameters
    ----------
    input_data : np.ndarray
        The input ramp data array of shape (Nreads, Ny, Nx).
    input_dq_raw : np.ndarray
        The input DQ_RAW array of shape (Nreads, Ny, Nx).
    input_dq : np.ndarray
        The input DQ array of shape (Ny, Nx).
    sat_thresh : np.ndarray
        The saturation threshold map of shape (Ny, Nx).
    sat_dq : np.ndarray
        The DQ map from the saturation model of shape (Ny, Nx).
    max_cores : int
        The maximum number of CPU cores to use.

    Returns
    -------
    input_dq_raw : np.ndarray
        The updated DQ_RAW array with saturation flags applied.
    input_dq : np.ndarray
        The updated DQ array with saturation flags applied.
    """
    with numba_thread_scope(max_cores):
        _check_saturation_numba(
            input_data, input_dq_raw, input_dq,
            sat_thresh, sat_dq,
        )
    return input_dq_raw, input_dq

@njit(nogil=True, parallel=True, cache=True)
def _check_saturation_numba(data, dq_raw, dq, sat_thresh, sat_dq):
    n_read, ny, nx = data.shape
    for j in prange(ny):  # parallelize over spatial rows
        for i in range(nx):
            thresh = sat_thresh[j, i]
            dq[j, i] |= sat_dq[j, i]
            for r in range(n_read):
                if data[r, j, i] >= thresh:
                    dq_raw[r::, j, i] |= (SATURATED_FLAG_uint8 | DO_NOT_USE_FLAG_uint8)
                    break