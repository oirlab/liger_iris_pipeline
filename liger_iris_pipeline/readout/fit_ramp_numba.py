from numba import jit, njit, prange
import numpy as np

# TODO: Implement jump detection, look into more sophisticated methods


def _fit_ramp_utr_loop_experimental(times, ramp):
    n_reads = len(times)
    for i in range(n_reads):
        xymult = times[i] * ramp[i]
        x2 = times[i] * times[i]
        tisi = tisi + xymult
        ti = ti + times[i]
        si = si + ramp[i]
        ti2 = ti2 + x2
    slope = (((n_reads * tisi) - (ti * si)) / ((n_reads * ti2) - (ti * ti)))
    return slope

@njit
def fit_ramp_utr(times, ramp):
    n_reads = len(times)
    tr_tot = np.sum(times * ramp)
    times_tot = np.sum(times)
    ramp_tot = np.sum(ramp)
    times2_tot = np.sum(times ** 2)
    numerator = n_reads * tr_tot - times_tot * ramp_tot
    denominator = n_reads * times2_tot - times_tot ** 2
    slope = (numerator / denominator)
    return slope

@njit
def fit_ramps_utr(times, ramps):
    ny, nx, n_groups, _ = ramps.shape
    slope_image_groups = np.zeros((ny, nx, n_groups), dtype=np.float32)
    for i in range(ny):
        for j in range(nx):
            for k in range(n_groups):
                slope_image_groups[i, j, k] = fit_ramp_utr(times[k, :], ramps[i, j, k, :])
    slope_image = np.zeros((ny, nx), dtype=np.float32)
    for i in range(n_groups):
        slope_image += slope_image_groups[:, :, i]
    slope_image /= n_groups
    slope_errors = np.zeros_like(slope_image)
    return slope_image, slope_errors

###########################


@njit
def fit_ramp_mcds(times, ramp, num_coadd):
    n1 = np.sum(ramp[:num_coadd]) / num_coadd
    n2 = np.sum(ramp[-num_coadd:]) / num_coadd
    d1 = np.sum(times[:num_coadd]) / num_coadd
    d2 = np.sum(times[-num_coadd:]) / num_coadd
    slope = (n2 - n1) / (d2 - d1)
    return slope


@njit
def fit_ramps_mcds(times, ramps, num_coadd):
    ny, nx, n_groups, _ = ramps.shape
    slope_image_groups = np.zeros((ny, nx, n_groups), dtype=np.float32)
    for i in range(ny):
        for j in range(nx):
            for k in range(n_groups):
                slope_image_groups[i, j, k] = fit_ramp_mcds(times[k, :], ramps[i, j, k, :], num_coadd)
    slope_image = np.zeros((ny, nx), dtype=np.float32)
    for i in range(n_groups):
        slope_image += slope_image_groups[:, :, i]
    slope_image /= n_groups
    slope_errors = np.zeros_like(slope_image)
    return slope_image, slope_errors