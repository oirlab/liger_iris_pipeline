import numpy as np
from numba import njit



@njit(nogil=True)
def weighted_mean(x, w):
    """
    Computes the weighted mean of a dataset.

    Args:
        x (np.ndarray): The input array.
        w (np.ndarray): The input weights, same shape as x.
        axis (int): Axis or tuple of axes along which to compute the mean. Default is None.

    Returns:
        float: The weighted mean.
    """
    return np.nansum(x * w) / np.nansum(w)


@njit(nogil=True)
def mad(x : np.ndarray):
    return np.nanmedian(np.abs(x - np.nanmedian(x)))


@njit(nogil=True)
def weighted_stddev(x : np.ndarray, w : np.ndarray, mu : float | None = None):
    """
    Calculate the weighted standard deviation of an array.
    
    Parameters:
    - x: Array of values
    - w: Array of weights
    
    Returns:
    - Weighted standard deviation or NaN if no valid data
    """
    w = w / np.nansum(w)
    if mu is None:
        mu = np.sum(x * w)
    dev = x - mu
    bias_estimator = 1.0 - np.nansum(w**2)
    var = np.nansum(dev ** 2 * w) / bias_estimator
    return np.sqrt(var)


@njit
def weighted_quantile(values : np.ndarray, weights : np.ndarray, q : float = 0.5):

    if len(values.shape) > 1:
        values = values.ravel()
        weights = weights.ravel()
    
    # Handle edge cases for q=0 and q=1
    if q == 0:
        return np.min(values)
    if q == 1:
        return np.max(values)
    
    sorted_indices = np.argsort(values)
    sorted_values = values[sorted_indices]
    sorted_weights = weights[sorted_indices]
    
    total_weight = np.sum(sorted_weights)
    target_weight = q * total_weight
    
    weight_sum = 0.0
    i = 0
    
    while i < len(sorted_weights) and weight_sum < target_weight:
        weight_sum += sorted_weights[i]
        i += 1
    
    if weight_sum == target_weight and i < len(sorted_weights):
        return (sorted_values[i-1] + sorted_values[i]) / 2.0
    elif i > 0:
        return sorted_values[i-1]
    else:
        return sorted_values[0]
    


@njit
def robust_stddev(x, w=None, n_sigma=4):
    """
    Calculate robust standard deviation using outlier rejection.
    
    Parameters:
    - x: Array of values
    - w: Array of weights (default: uniform weights)
    - n_sigma: Number of sigma for outlier rejection
    
    Returns:
    - Robust standard deviation or NaN if insufficient valid data
    """
    if w is None:
        w = np.ones(x.shape)
    
    # Calculate median
    med = weighted_quantile(x, w)
    
    # Calculate absolute deviations
    adevs = np.abs(med - x)
    
    # Calculate MAD (Median Absolute Deviation)
    mad = weighted_quantile(adevs, w)
    
    # Find indices for outlier rejection
    good = np.zeros(len(x), dtype=np.bool_)
    for i in range(len(x)):
        good[i] = adevs[i] < 1.4826 * mad * n_sigma
    
    # Filter out outliers
    x_good = x[good]
    w_good = w[good]
    
    if len(x_good) > 1:
        return weighted_stddev(x_good, w_good)
    else:
        return np.nan

@njit
def robust_mean(x, w=None, n_sigma=4):
    """
    Calculate robust mean using outlier rejection.
    
    Parameters:
    - x: Array of values
    - w: Array of weights (default: uniform weights)
    - n_sigma: Number of sigma for outlier rejection
    
    Returns:
    - Robust mean or NaN if insufficient valid data
    """
    if w is None:
        w = np.ones(x.shape)
    
    # Calculate median
    med = weighted_quantile(x, w)
    
    # Calculate absolute deviations
    adevs = np.abs(med - x)
    
    # Calculate MAD (Median Absolute Deviation)
    mad = weighted_quantile(adevs, w)
    
    # Find indices for outlier rejection
    good = np.zeros(len(x), dtype=np.bool_)
    for i in range(len(x)):
        good[i] = adevs[i] < 1.4826 * mad * n_sigma
    
    # Filter out outliers
    x_good = x[good]
    w_good = w[good]
    
    if len(x_good) > 1:
        return np.sum(x_good * w_good) / np.sum(w_good)
    else:
        return np.nan