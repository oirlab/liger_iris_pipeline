import numpy as np
from numba import njit
from . import math


@njit(nogil=True)
def _propagate_error(error : np.ndarray) -> float:
    """
    Propagate individual errors in quadrature.

    Args:
        error (np.ndarray): The error array.
        dq (np.ndarray): The data quality array.
    
    Returns:
        float: The propagated error.
    """
    return np.sum(1 / error**2)**-0.5


@njit(nogil=True)
def propagate_error(error : np.ndarray, dq : np.ndarray) -> float:
    """
    Propagate individual errors in quadrature. First checks for good values according to the data quality array.

    Args:
        error (np.ndarray): The error array.
        dq (np.ndarray): The data quality array.
    
    Returns:
        float: The propagated error.
    """
    error = error.ravel()
    dq = dq.ravel()
    mask = dq == 0
    if math.any_sc(mask):
        return _propagate_error(error[mask])
    else:
        return np.nan


@njit(nogil=True)
def _measure_error(data : np.ndarray, error : np.ndarray, M : float | None = None) -> float:
    weights = 1 / error**2
    error = math.weighted_stddev(data, weights, M=M)
    error /= np.sqrt(data.size - 1)
    return error


@njit(nogil=True)
def measure_error(data : np.ndarray, error : np.ndarray, dq : np.ndarray) -> float:
    error = error.ravel()
    dq = dq.ravel()
    mask = dq == 0
    n_good = np.sum(mask)
    if n_good == 0:
        return np.nan
    elif n_good == 1:
        return error[mask][0]
    else:
        return _measure_error(data[mask], error[mask])