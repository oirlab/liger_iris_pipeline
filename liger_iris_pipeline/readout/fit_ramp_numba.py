from numba import njit
import numpy as np

# TODO: Implement jump detection, look into more sophisticated methods

@njit(nogil=True)
def _fit_ramp_ols(times, ramp):
    """
    Fits a line to the given data (times, ramp) with a free y-intercept.

    Args:
        times (np.ndarray): The times at which the data was taken.
        ramp (np.ndarray): The ramp data.

    Returns:
        tuple[float, float] : slope and slope error
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
    
    # Return slope and slope error
    return slope, slope_err


@njit(nogil=True)
def _fit_ramps_ols(times, ramps):
    ny, nx, n_groups, _ = ramps.shape
    slope = np.zeros((ny, nx), dtype=np.float32)
    slope_error = np.zeros((ny, nx), dtype=np.float32)
    slope_groups = np.zeros(n_groups, dtype=np.float32)
    slope_error_groups = np.zeros(n_groups, dtype=np.float32)
    for i in range(ny):
        for j in range(nx):
            for k in range(n_groups):
                slope_groups[k], slope_error_groups[k] = _fit_ramp_ols(times[k, :], ramps[i, j, k, :])
            slope[i, j], slope_error[i, j] = _combine_group_slopes(slope_groups, slope_error_groups)
    return slope, slope_error


@njit(nogil=True)
def _combine_group_slopes(slopes, slope_errors):
    if slope_errors[0] == 0:
        return slopes[0], slope_errors[0] # NOTE: This will fail if some errors are zero, moving to jwst alg soon anyway...
    else:
        w = 1 / slope_errors**2
        slope_combined = np.sum(slopes * w) / np.sum(w)
        slope_error_combined = np.sqrt(1 / np.sum(slope_errors**2))
        return slope_combined, slope_error_combined

@njit(nogil=True)
def fit_ramps_ols(times, ramps):
    """
    Top-level function for fitting ramps.

    Args:
        times (np.ndarray): Read times.
        ramps (np.ndarray): 4D array of ramp data with shape (ny, nx, n_groups, n_reads).

    Returns:
        dict[str, np.ndarray]: Dictionary with keys 'slope' and 'slope_err'.
    """
    return _fit_ramps_ols(times, ramps)


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
            slope[i, j], slope_error[i, j] = _combine_group_slopes(slope_groups, slope_error_groups)
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
    return _fit_ramps_mcds(times, ramps, num_coadd=num_coadd)