from numba import njit, prange
import numpy as np

__all__ = ['correct_nonlinearity']


@njit
def correct_nonlinearity(ramps, coeffs):
    ny, nx, n_groups, _ = ramps.shape
    for i in range(ny):
        for j in range(nx):
            for k in range(n_groups):
                ramps[i, j, k, :] = polyval(coeffs[i, j, :], ramps[i, j, k, :])
    return ramps


@njit
def polyval(coeffs, x):
    v = np.zeros_like(x)
    for coeff in coeffs[::-1]:
        v = v * x + coeff
    return v