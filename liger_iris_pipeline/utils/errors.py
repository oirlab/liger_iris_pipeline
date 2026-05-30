import numpy as np
from numba import njit
from .math import any_sc, weighted_stddev


@njit(nogil=True)
def measure_error(data : np.ndarray, error : np.ndarray, mask : np.ndarray) -> float:
    """
    Measure the error from a set of data points from the weighted stddev.

    Parameters
    ----------
    data : np.ndarray
        Data array.
    error : np.ndarray
        Error array.
    mask : np.ndarray
        Boolean mask indicating good values to include.
    """
    data = data.ravel()
    error = error.ravel()
    mask = mask.ravel()
    n_good = np.sum(mask)
    if n_good == 0:
        return np.nan
    elif n_good == 1:
        return error[mask][0]
    else:
        weights = 1 / error**2
        weights[~mask] = 0
        error = weighted_stddev(data, weights)
        error /= np.sqrt(n_good - 1)
        return error
    

@njit(nogil=True)
def propagate_error(error : np.ndarray, mask : np.ndarray) -> float:
    """
    Propagate individual errors in quadrature.

    Parameters
    ----------
    error : np.ndarray
        Error array.
    mask : np.ndarray
        Boolean mask indicating good values to include.
    
    Returns
    -------
    float
        The propagated error.
    """
    if any_sc(mask):
        return np.sum(1 / error[mask]**2)**-0.5
    else:
        return np.nan
    

@njit(nogil=True)
def propagate_variance(var : np.ndarray, mask : np.ndarray) -> float:
    """
    Propagate variance values in quadrature.

    Parameters
    ----------
    var : np.ndarray
        Variance array.
    mask : np.ndarray
        Boolean mask indicating good values to include.

    Returns
    -------
    float
        The propagated variance.
    """

    if any_sc(mask):
        return np.sum(1 / var[mask])**-1
    else:
        return np.nan