from ..stpipe.base_step import LigerIRISStep
from .. import datamodels
from ..utils.subarray import get_subarray_model
from ..utils.parallelization_utils import numba_thread_scope
from ..calibrations import DetectorFlatSelector

from numba import njit, prange
import numpy as np
import logging

logger = logging.getLogger(__name__)


__all__ = ["DetectorFlatStep"]


class DetectorFlatStep(LigerIRISStep):
    """
    The appropriate master detflat calibration is divided into the input data.
    The input's ``err`` attribute is updated by adding the flat ``err`` attribute in quadarature.
    DQ flags are updated with bitwise or.


    Parameters
    ----------
    input : ImagerModel
        Input imager data model
    max_cores : int, optional
        Maximum number of CPU cores to use.
        Default is 1.

    Calibrations
    ------------
    detflat : DetectorFlatModel

    Returns
    -------
    output
        Flat-fielded corrected data model (same type as input).
    """

    spec = """
        max_cores = integer(default=1) # Number of CPU cores to use for processing
    """

    calibrations = {
        'detflat' : {
            'selector' : DetectorFlatSelector,
            'selector_kwargs' : {}
        }
    }
    class_alias = "detflat"

    def process(self, input):

        # Open the input data model
        input_model = self.open_model(input)

        # Get the name of the flat reference file to use
        flat_ref, _ = self.get_calibration(input_model, "detflat")
        logger.info(f"Using detflat reference: {flat_ref}")

        # Open the flat reference data model and apply it
        with self.open_model(flat_ref) as flat_model:
            
            # Get the subarray model
            flat_model_subarr = get_subarray_model(input_model, flat_model)

            # Do the flat-field correction
            detector_flat_correction(
                input_model.data, input_model.err,
                input_model.var_poisson, input_model.var_rnoise,
                input_model.dq,
                flat_model_subarr.data, flat_model_subarr.err, flat_model_subarr.dq,
                max_cores=self.max_cores
            )

        # Return the flat-fielded data model
        return input_model
    

def detector_flat_correction(
    input_rate : np.ndarray, input_err : np.ndarray,
    input_var_poisson : np.ndarray, input_var_rnoise : np.ndarray,
    input_dq : np.ndarray,
    detflat : np.ndarray, detflat_err : np.ndarray, detflat_dq : np.ndarray,
    max_cores : int = 1
):
    """
    Correct the detector level flat field.

    Parameters
    ----------
    input_rate : ndarray
        The input rate image to be corrected.
    input_err : ndarray
        The error associated with the input rate image.
    input_dq : ndarray
        The data quality array associated with the input rate image.
    detflat : ndarray
        The detector flat field image.
    detflat_err : ndarray
        The error associated with the detector flat field image.
    detflat_dq : ndarray
        The data quality array associated with the detector flat field image.
    max_cores : int
        The number of CPU cores to use for processing.
    
    Returns
    -------
    input_rate : ndarray
        Input rate image (DN/s) with flat-field correction applied.
    input_err : ndarray
        Input error image (DN/s) with flat-field correction applied.
    input_dq : ndarray
        Input data quality image with flat-field correction applied.
    """
    with numba_thread_scope(max_cores):
        _detector_flat_correction_numba(
            input_rate, input_err,
            input_var_poisson, input_var_rnoise,
            input_dq,
            detflat, detflat_err, detflat_dq
        )
    return input_rate, input_err, input_dq


@njit(nogil=True, parallel=True, cache=True)
def _detector_flat_correction_numba(
    input_rate : np.ndarray, input_err : np.ndarray,
    input_var_poisson : np.ndarray, input_var_rnoise : np.ndarray,
    input_dq : np.ndarray,
    detflat : np.ndarray, detflat_err : np.ndarray, detflat_dq : np.ndarray
):
    ny, nx = input_rate.shape
    for j in prange(ny):
        for i in range(nx):
            f = detflat[j, i]
            r = input_rate[j, i]
            if f > 0:
                input_rate[j, i] = r / f
                input_var_poisson[j, i] = input_var_poisson[j, i] / f
                input_var_rnoise[j, i] = input_var_rnoise[j, i] / f
            z = np.abs(r)
            _input_err = input_err[j, i]
            _flat_err = detflat_err[j, i]

            # approximate error propagation for division of random variables
            # https://en.wikipedia.org/wiki/Propagation_of_uncertainty
            if r > 0 and f > 0:
                input_err[j, i] = z * np.sqrt((_input_err / r) ** 2 + (_flat_err / f) ** 2)

            # Update DQ
            input_dq[j, i] |= detflat_dq[j, i]