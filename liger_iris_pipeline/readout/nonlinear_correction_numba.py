from numba import jit, njit, prange
import numpy as np

@njit
def correct_nonlinearity(times, ramps, coeffs):
    ny, nx, n_groups, n_reads_per_group = ramps.shape
    ramps_out = np.zeros_like(ramps)
    for i in range(ny):
        for j in range(nx):
            for k in range(n_groups):
                for l in range(n_reads_per_group):
                    v = polyval(coeffs[i, j, :], times[k, l])
                    if v != 0:
                        ramps_out[i, j, k, l] = ramps[i, j, k, l] / v
    return ramps_out

@njit
def polyval(coeffs, x):
    v = np.float32(0)
    for i in range(len(coeffs)):
        v += coeffs[i] * (x ** i)
    return v