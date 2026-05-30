import numpy as np
from numba import njit, prange
from ..utils.parallelization_utils import numba_thread_scope

def dark_subtraction_rate(
    input_rate: np.ndarray, input_err: np.ndarray, input_dq: np.ndarray,
    dark_rate: np.ndarray, dark_err: np.ndarray, dark_dq: np.ndarray,
    max_cores : int = 1
):
    """
    Subtract the dark current rate from the input rate.
    Add the dark error in quadrature to the input error.
    Update the input DQ flags with the dark DQ flags using bitwise OR.

    Parameters
    ----------
    input_rate : np.ndarray
        2D array of rate values (DN/s)
    input_err : np.ndarray
        2D array of error values (DN/s)
    input_dq : np.ndarray
        2D array of data quality flags
    dark_rate : np.ndarray
        2D array of dark rate values (DN/s)
    dark_err : np.ndarray
        2D array of dark error values (DN/s)
    dark_dq : np.ndarray
        2D array of dark data quality flags
    max_cores : int
        Maximum number of CPU cores to use for parallel processing.

    Returns
    -------
    input_rate : np.ndarray
        Dark-subtracted rate array (modified in place)
    input_err : np.ndarray
        Updated error array (modified in place)
    input_dq : np.ndarray
        Updated data quality array (modified in place)
    """
    with numba_thread_scope(max_cores):
        _dark_subtraction_rate_numba(
            input_rate, input_err, input_dq,
            dark_rate, dark_err, dark_dq
        )
    return input_rate, input_err, input_dq


@njit(nogil=True, parallel=True, cache=True)
def _dark_subtraction_rate_numba(
    input_rate : np.ndarray, input_err : np.ndarray, input_dq : np.ndarray,
    dark_rate : np.ndarray, dark_err : np.ndarray, dark_dq : np.ndarray
):
    ny, nx = input_rate.shape
    for j in prange(ny):
        for i in range(nx):
            # Subtract dark rate
            input_rate[j, i] = input_rate[j, i] - dark_rate[j, i]

            # Propagate error
            input_err[j, i] = np.sqrt(input_err[j, i] * input_err[j, i] + dark_err[j, i] * dark_err[j, i])

            # Propagate DQ
            input_dq[j, i] |= dark_dq[j, i]