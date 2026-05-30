from ..stpipe.base_step import LigerIRISStep
import numpy as np
from numba import njit, prange
from ..utils.parallelization_utils import numba_thread_scope
from ..calibrations import GainSelector
from ..utils.subarray import get_subarray_model

import logging

logger = logging.getLogger(__name__)

__all__ = ["GainStep"]


class GainStep(LigerIRISStep):
    """
    GainStep: Performs detector gain correction.

    Parameters
    ----------
    input : RampModel
        Input ramp model to apply gain correction to.
    max_cores : int, optional
        Maximum number of CPU cores to use.
        Default is 1.
    """

    calibrations = {
        'gain' : {
            'selector': GainSelector,
            'selector_kwargs': {}
        }
    }
    class_alias = "gain"

    def process(self, input):

        # Open the input data model
        input_model = self.open_model(input)

        # Get the name of the gain reference file to use
        gain_ref, _ = self.get_calibration(input_model, "gain")
        logger.info(f"Using gain reference {gain_ref}")

        with self.open_model(gain_ref) as gain_model:

            # Get subarray model if needed
            gain_model_subarray = get_subarray_model(input_model, gain_model)

            # Do the gain correction
            gain_correction(
                input_model.data,
                input_model.err,
                input_model.var_rnoise,
                input_model.var_poisson,
                input_model.dq,
                gain_model_subarray.gain,
                np.sqrt(gain_model_subarray.cov[0, 0]),
                gain_model_subarray.dq,
            )

        # Return the corrected data model
        return input_model


# def gain_correction(
#     input_rate : np.ndarray, input_err : np.ndarray, input_dq : np.ndarray,
#     gain : np.ndarray, gain_err : np.ndarray, gain_dq : np.ndarray
# ):
#     # Apply the detector gain correction
#     input_rate *= gain

#     # Propagate the errors and DQ flags
#     gr = np.abs(input_rate)
#     r  = input_rate / gain
#     g  = gain

#     input_err[:] = gr * np.sqrt((input_err / r)**2 + (gain_err / g)**2)

#     input_dq |= gain_dq

def gain_correction(
    input_rate : np.ndarray, input_err : np.ndarray,
    input_var_rnoise : np.ndarray, input_var_poisson : np.ndarray,
    input_dq : np.ndarray,
    gain : np.ndarray, gain_err : np.ndarray, gain_dq : np.ndarray,
    max_cores : int = 1
):
    """
    Apply detector gain correction to 2D rate image.

    Parameters
    ----------
    input_rate : np.ndarray
        2D array of input rates.
    input_err : np.ndarray
        2D array of input rate errors.
    input_var_rnoise : np.ndarray
        2D array of input read noise variances.
    input_var_poisson : np.ndarray
        2D array of input Poisson variances.
    input_dq : np.ndarray
        2D array of input data quality flags.
    gain : np.ndarray
        2D array of gain values.
    gain_err : np.ndarray
        2D array of gain errors.
    gain_dq : np.ndarray
        2D array of gain data quality flags.
    max_cores : int, optional
        Maximum number of CPU cores to use for parallel processing. Default is 1.

    Returns
    -------
    input_rate : np.ndarray
        Gain-corrected rate array.
    input_err : np.ndarray
        Updated rate error array.
    input_dq : np.ndarray
        Updated data quality flags array.
    """
    with numba_thread_scope(max_cores):
        _gain_correction_numba(
            input_rate, input_err,
            input_var_rnoise, input_var_poisson,
            input_dq,
            gain, gain_err, gain_dq
        )
    return input_rate, input_err, input_dq


@njit(nogil=True, parallel=True, cache=True)
def _gain_correction_numba(
    input_rate : np.ndarray,
    input_err : np.ndarray,
    input_var_rnoise : np.ndarray,
    input_var_poisson : np.ndarray,
    input_dq : np.ndarray,
    gain : np.ndarray, gain_err : np.ndarray, gain_dq : np.ndarray
):
    ny, nx = input_rate.shape
    for j in prange(ny):
        for i in range(nx):
            g = gain[j, i]
            r = input_rate[j, i]
            input_rate[j, i] = r * g
            gr = np.abs(input_rate[j, i])
            e_in = input_err[j, i]
            ge_in = gain_err[j, i]

            # Approximate error propagation for division of random variables
            # https://en.wikipedia.org/wiki/Propagation_of_uncertainty
            input_err[j, i] = gr * np.sqrt((e_in / r) ** 2 + (ge_in / g) ** 2)

            input_var_poisson[j, i] *= gr**2
            input_var_rnoise[j, i] *= g**2

            input_dq[j, i] |= gain_dq[j, i]