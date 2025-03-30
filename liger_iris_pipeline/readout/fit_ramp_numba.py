from numba import njit
import numpy as np

# TODO: Implement jump detection, look into more sophisticated methods

@njit(nogil=True)
def _fit_ramp_slope_intercept_ols(times, ramp):
    """
    Fits a line to the given data (times, ramp) with a free y-intercept.

    Args:
        times (np.ndarray): The times at which the data was taken.
        ramp (np.ndarray): The ramp data.

    Returns:
        float32: slope
        float32: slope error
        float32: y-intercept
        float32: y-intercept error
    """
    n = len(times)
    times_tot = np.sum(times)
    times2_tot = np.sum(times**2)
    ramp_tot = np.sum(ramp)
    
    slope = (n * np.sum(times * ramp) - times_tot * ramp_tot) / (n * times2_tot - times_tot**2)
    b = (ramp_tot - slope * times_tot) / n
    
    # Compute residual variance
    residual_var = np.sum((ramp - slope * times - b)**2) / (n - 2)
    
    # Compute errors
    slope_err = np.sqrt(residual_var / (times2_tot - times_tot**2 / n))
    b_err = np.sqrt(residual_var * times2_tot / (n * (times2_tot - times_tot**2 / n)))
    
    return slope, slope_err, b, b_err


@njit(nogil=True)
def _fit_ramp_slope_fixed_intercept_ols(times, ramp, b):
    """
    Fits a line to the given data (times, ramp) with a fixed y-intercept.

    Args:
        times (np.ndarray): The read times (1D).
        ramp (np.ndarray): The ramp data (1D).
        fixed_intercept (float32): The fixed y-intercept value.

    Returns:
        float32: slope
        float32: slope error
    """
    n = len(times)
    times2_tot = np.sum(times**2)
    slope = np.sum(times * (ramp - b)) / times2_tot
    residual_var = np.sum((ramp - slope * times - b)**2) / (n - 1)
    slope_err = np.sqrt(residual_var / times2_tot)
    return slope, slope_err


@njit(nogil=True)
def _fit_ramps_slope_intercept_ols(times, ramps):
    ny, nx, n_groups, _ = ramps.shape
    slope = np.zeros((ny, nx), dtype=np.float32)
    slope_error = np.zeros((ny, nx), dtype=np.float32)
    b = np.zeros((ny, nx), dtype=np.float32)
    b_error = np.zeros((ny, nx), dtype=np.float32)
    slope_groups = np.zeros(n_groups, dtype=np.float32)
    slope_error_groups = np.zeros(n_groups, dtype=np.float32)
    b_groups = np.zeros(n_groups, dtype=np.float32)
    b_error_groups = np.zeros(n_groups, dtype=np.float32)
    for i in range(ny):
        for j in range(nx):
            for k in range(n_groups):
                slope_groups[k], slope_error_groups[k], b_groups[k], b_error_groups[k] = _fit_ramp_slope_intercept_ols(times[k, :], ramps[i, j, k, :])
            slope[i, j], slope_error[i, j] = combine_group_slopes(slope_groups, slope_error_groups)
            b[i, j], b_error[i, j] = combine_group_intercepts(b, b_error)
    return slope, slope_error, b, b_error

@njit(nogil=True)
def combine_group_slopes(slope, slope_error):
    slope_combined = np.mean(slope)
    return slope_combined, np.zeros_like(slope_combined)


@njit(nogil=True)
def combine_group_intercepts(b, b_error):
    b_combined = np.mean(b)
    return b_combined, np.zeros_like(b_combined)


# #@njit(nogil=True)
# def combine_group_slopes(slope, slope_error):
#     w = 1 / slope_error**2
#     slope_combined = np.sum(slope * w, axis=2) / np.sum(w, axis=2)
#     slope_error_combined = np.sqrt(1 / np.sum(w, axis=2))
#     return slope_combined, slope_error_combined


# #@njit(nogil=True)
# def combine_group_intercepts(b, b_error):
#     w = 1 / b_error**2
#     b_combined = np.sum(b * w, axis=2) / np.sum(w, axis=2)
#     b_error_combined = np.sqrt(1 / np.sum(w, axis=2))
#     return b_combined, b_error_combined
    

@njit(nogil=True)
def _fit_ramps_slope_fixed_intercept_ols(times, ramps, b):
    ny, nx, n_groups, _ = ramps.shape
    slope = np.zeros((ny, nx), dtype=np.float32)
    slope_error = np.zeros((ny, nx), dtype=np.float32)
    slope_groups = np.zeros(shape=(ny, nx, n_groups), dtype=np.float32)
    slope_error_groups = np.zeros(shape=(ny, nx, n_groups), dtype=np.float32)
    for i in range(ny):
        for j in range(nx):
            for k in range(n_groups):
                slope_groups[i, j, k], slope_error_groups[i, j, k] = _fit_ramp_slope_fixed_intercept_ols(times[k, :], ramps[i, j, k, :], b[i, j])
            slope[i, j], slope_error[i, j] = combine_group_slopes(slope_groups, slope_error_groups)
    return slope, slope_error


def fit_ramps_ols(times, ramps, b=None):
    """
    Top-level function for fitting ramps with or without a fixed y-intercept with no correlated noise.

    Args:
        times (np.ndarray): Read times.
        ramps (np.ndarray): 4D array of ramp data with shape (ny, nx, n_groups, n_reads).
        b (np.ndarray, optional): Fixed y-intercept value. If None, y-intercept will be fit.

    Returns:
        dict[str, np.ndarray]: Dictionary with keys 'slope' and 'slope_err' containing the fitted slopes and errors. If b is not provided, the result also contains 'b' and 'b_err'.
    """
    if b is None:
        result = _fit_ramps_slope_intercept_ols(times, ramps)
        return dict(slope=result[0], slope_error=result[1], b=result[2], b_error=result[3])
    
    if not isinstance(b, np.ndarray):
        b = np.full(b, dtype=np.float32)

    result = _fit_ramps_slope_fixed_intercept_ols(times, ramps, b)
    return dict(slope=result[0], slope_error=result[1])


@njit(nogil=True)
def _fit_ramp_mcds(times, ramp, num_coadd=1):
    n = len(times)
    n1 = np.sum(ramp[:num_coadd])
    n2 = np.sum(ramp[-num_coadd:])
    d1 = np.sum(times[:num_coadd])
    d2 = np.sum(times[-num_coadd:])
    if num_coadd > 1:
        n1 = n1 / num_coadd
        n2 = n2 / num_coadd
        d1 = d1 / num_coadd
        d2 = d2 / num_coadd
    slope = (n2 - n1) / (d2 - d1)
    residuals = ramp - slope * times
    slope_err = np.sqrt(np.sum(residuals**2) / (n - 1) / np.sum(times**2))
    return slope, slope_err

@njit(nogil=True)
def _fit_ramps_mcds(times, ramps, num_coadd=1):
    ny, nx, n_groups, _ = ramps.shape
    slope = np.zeros((ny, nx), dtype=np.float32)
    slope_error = np.zeros((ny, nx), dtype=np.float32)
    slope_groups = np.zeros(shape=n_groups, dtype=np.float32)
    slope_error_groups = np.zeros(shape=n_groups, dtype=np.float32)
    for i in range(ny):
        for j in range(nx):
            for k in range(n_groups):
                slope_groups[k], slope_error_groups[k] = _fit_ramp_mcds(times[k, :], ramps[i, j, k, :], num_coadd=num_coadd)
            slope[i, j], slope_error[i, j] = combine_group_slopes(slope_groups, slope_error_groups)
    return slope, slope_error


def fit_ramps_mcds(times, ramps, num_coadd=1):
    """
    Fits ramps using the (M)CDS method.

    Args:
        times (np.ndarray): Read times.
        ramps (np.ndarray): 3D array of ramp data with shape (ny, nx, n_reads, n_groups).
        num_coadd (int): Number of coadds. num_coadd=1 for CDS.

    Returns:
        dict[str, np.ndarray]: Dictionary with keys 'slope' and 'slope_err' containing the fitted slopes and errors.
    """
    result = _fit_ramps_mcds(times, ramps, num_coadd=num_coadd)
    return dict(slope=result[0], slope_error=result[1])