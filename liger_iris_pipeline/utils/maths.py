import numpy as np
from numba import njit


@njit
def weighted_stddev(x, w, mu=None):
    """
    Calculate the weighted standard deviation of an array.
    
    Parameters:
    - x: Array of values
    - w: Array of weights
    - mu: Optional pre-calculated weighted mean
    
    Returns:
    - Weighted standard deviation or NaN if no valid data
    """
    # Find indices where x and w are valid
    good = np.zeros(len(x), dtype=np.bool_)
    for i in range(len(x)):
        good[i] = np.isfinite(x[i]) and (w[i] > 0) and np.isfinite(w[i])
    
    # Extract valid values
    xx = x[good]
    ww = w[good]
    
    if len(xx) == 0:
        return np.nan
    
    # Normalize weights
    ww_sum = np.sum(ww)
    ww = ww / ww_sum
    
    # Calculate weighted mean if not provided
    if mu is None:
        mu = nansum(xx * ww) / nansum(ww)
    
    # Calculate deviation from mean
    dev = xx - mu
    
    # Calculate bias estimator
    bias_estimator = 1.0 - np.sum(ww**2)
    
    # Calculate standard deviation
    sigma = np.sqrt(np.sum(dev**2 * ww) / bias_estimator)
    
    return sigma

@njit
def weighted_quantile(x, w, q=0.5):
    """
    Calculate the weighted quantile of an array.
    
    Parameters:
    - x: Array of values
    - w: Array of weights
    - q: Quantile to calculate (default: 0.5 for median)
    
    Returns:
    - Weighted quantile or NaN if no valid data
    """
    # Find indices where x and w are valid
    good = np.zeros(len(x), dtype=np.bool_)
    for i in range(len(x)):
        good[i] = np.isfinite(x[i]) and (w[i] > 0) and np.isfinite(w[i])
    
    # Extract valid values
    xx = x[good]
    ww = w[good]
    
    if len(xx) == 0:
        return np.nan
    
    # Sort by values
    idx = np.argsort(xx)
    sorted_x = xx[idx]
    sorted_w = ww[idx]
    
    # Calculate cumulative weights
    cum_weights = np.cumsum(sorted_w)
    cum_weights = cum_weights / cum_weights[-1]  # Normalize to 1
    
    # Find index where cumulative weight exceeds q
    i = np.searchsorted(cum_weights, q, side='right')
    
    # Handle edge cases
    if i == 0:
        return sorted_x[0]
    elif i == len(sorted_x):
        return sorted_x[-1]
    else:
        # Linear interpolation
        return sorted_x[i-1]

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