import numpy as np
from numba import njit

@njit(nogil=True)
def weighted_mean(x, w):
    return np.nansum(x * w) / np.nansum(w)


@njit(nogil=True)
def weighted_stddev(x : np.ndarray, w : np.ndarray, center : float | None = None):
    w = w / np.nansum(w)
    if center is None:
        center = np.sum(x * w)
    dev = x - center
    bias_estimator = 1.0 - np.nansum(w**2)
    var = np.nansum(dev ** 2 * w) / bias_estimator
    return np.sqrt(var)


@njit(nogil=True)
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
    


@njit(nogil=True)
def robust_stddev(x, w=None, n_sigma=4):
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

@njit(nogil=True)
def robust_mean(x, w=None, n_sigma=4):
    """
    Calculate robust mean using outlier rejection.
    
    Parameters
    ----------
    x : np.ndarray
        Array of values.
    w : np.ndarray, optional
        Array of weights (default: uniform weights).
    n_sigma : float, optional
        Number of sigma for outlier rejection (default: 4).

    Returns
    -------
    float
        Robust mean or NaN if insufficient valid data.
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


@njit(nogil=True)
def median_absolute_deviation(data : np.ndarray, center : float | None = None):
    if center is None:
        center = np.nanmedian(data)
    return np.nanmedian(np.abs(data - center))


@njit(nogil=True)
def biweight_location(
    data : np.ndarray,
    c : float = 6.0,
    center : float | None = None
) -> float:
    
    # Flatten
    data = data.ravel()

    # Median value
    if center is None:
        center = np.nanmedian(data)

    # MAD
    mad = median_absolute_deviation(data, center)
    if mad == 0.0 or not np.isfinite(mad):
        return center

    # Center the data
    n = data.size
    result_num = 0
    result_den = 0
    for i in range(n):
        u = (data[i] - center) / (c * mad)
        if np.abs(u) < 1:
            w = (1 - u**2)**2
            result_num += (data[i] - center) * w
            result_den += w

    if result_den == 0:
        return center

    return center + result_num / result_den


@njit(nogil=True)
def biweight_midvariance(
    data : np.ndarray,
    c : float = 9.0,
    center : float | None = None,
) -> float:
    
    # Flatten
    data = data.ravel()

    # Median value
    if center is None:
        center = np.nanmedian(data)

    # Center the data
    d = data - center
    mad_val = median_absolute_deviation(data, center)

    if mad_val == 0.0 or not np.isfinite(mad_val):
        return mad_val

    u = d / (c * mad_val)
    u2 = u * u

    good = np.where((np.abs(u) < 1.0) & np.isfinite(u))[0]
    n_good = len(good)

    f1 = 0
    f2 = 0
    for i in range(n_good):
        ii = good[i]
        t = 1 - u2[ii]
        f1 += d[ii] * d[ii] * t ** 4
        f2 += t * (1.0 - 5.0 * u2[ii])
    return n_good * f1 / (f2 * f2)


@njit(nogil=True)
def any_sc(arr : np.ndarray) -> bool:
    """
    Optimized version of np.any which short circuits, unlike numpy.any.
    """
    for item in arr.ravel():
        if item:
            return True
    return False


@njit(nogil=True)
def all_sc(arr : np.ndarray) -> bool:
    """
    Optimized version of np.all which short circuits, unlike numpy.all.
    """
    for item in arr.ravel():
        if item:
            continue
        else:
            return False
    return True


@njit(nogil=True)
def polyval1d(coeffs : np.ndarray, x : np.ndarray) -> np.ndarray:
    """
    Evaluate a polynomial with given coefficients at specified points using the Horner method.

    Parameters
    ----------
    coeffs : np.ndarray
        Coefficients of the polynomial, ordered from lowest degree to highest (NOTE: numpy is reversed).
    x : np.ndarray
        Points at which to evaluate the polynomial.
    """
    v = np.zeros(x.shape, dtype=coeffs.dtype)
    for coeff in coeffs[::-1]:
        v = v * x + coeff
    return v