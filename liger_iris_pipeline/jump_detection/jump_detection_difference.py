from ..datamodels.dqflags import DQ_FLAGS
from ..utils.parallelization_utils import numba_thread_scope

import numpy as np
from numba import njit, prange

__all__ = ['jump_detection_difference']

SATURATED_FLAG_uint8 = np.uint8(DQ_FLAGS["SATURATED"])
DO_NOT_USE_FLAG_uint8 = np.uint8(DQ_FLAGS["DO_NOT_USE"])
JUMP_DET_FLAG_uint8 = np.uint8(DQ_FLAGS["JUMP_DET"])

@njit(nogil=True, cache=True, inline='always')
def get_diffs(ramp_row):
    n_reads, nx = ramp_row.shape
    diffs = np.empty((n_reads-1, nx), dtype=ramp_row.dtype)
    for i in range(n_reads - 1):
        diffs[i] = ramp_row[i+1,:] - ramp_row[i,:]
    return diffs


@njit(nogil=True, cache=True, inline='always')
def median_axis0_3d(ramp):
    """
    Median along axis=0 for a 3D array shaped (n_reads, ny, nx).
    Returns NumPy's median on integer inputs.
    """
    n, ny, nx = ramp.shape
    out = np.empty((ny, nx), dtype=ramp.dtype)
    for y in range(ny):
        for x in range(nx):
            vec = np.empty(n, dtype=np.float64)
            for i in range(n):
                vec[i] = ramp[i, y, x]
            vec.sort()
            mid = n // 2
            if n % 2 == 0:
                out[y, x] = 0.5 * (vec[mid - 1] + vec[mid])
            else:
                out[y, x] = vec[mid]
    return out

@njit(nogil=True, parallel=True, cache=True)
def _jump_detection_difference_numba(ramp_data, dq_raw, dq, rdnoise, gain,rejection_threshold):
    n_reads, ny, nx = ramp_data.shape

    for i in prange(ny):
        for j in range(nx):
            # Find first saturated index; exclude it and everything after.
            n_use = 1
            for k in range(n_reads):
                # checking backward for saturation to speed up processing since saturation will be at the end of the ramp
                if (dq_raw[n_reads-k-1,i,j] & (SATURATED_FLAG_uint8 | DO_NOT_USE_FLAG_uint8)) == 0:
                    n_use = n_reads-k
                    break

            # Calculate differences between successive reads
            diffs = get_diffs(ramp_data[0:n_use,i,j:j+1])  # np.diff(ramp_data, axis=0)

            # Estimate the typical value of differences and the noise in the differences
            median_diff = median_axis0_3d(diffs[:,None,:])[0,0] * gain[i,j]  # np.median(diffs, axis=0) * gain
            photon_noise_squared = np.abs(median_diff)  # Assuming Poisson
            total_DN_noise_squared = (rdnoise[i,j] ** 2) * 2 + (photon_noise_squared / (gain[i,j]**2))  # Factor of 2 for diffs
            sigma_diff = np.sqrt(total_DN_noise_squared)   # Convert back to ADU

            # Identify jumps
            jumps = (np.abs(diffs[:,0]-median_diff) > (rejection_threshold * sigma_diff)).astype(np.uint8) * JUMP_DET_FLAG_uint8
            # Modify dq_out to flag where jumps occurred
            dq_raw[1:n_use, i, j] |= jumps

    return

def jump_detection_difference(
    ramp_data: np.ndarray,
    dq_raw: np.ndarray,
    dq: np.ndarray,
    rdnoise : np.ndarray | None = None,
    gain: np.ndarray | None = None,
    rejection_threshold: float = 4.0,
    max_cores: int = 1,
) -> np.ndarray:
    """
    Simple jump detection for a 3D array of up the ramp data.
    Modifies the input dq array (in-place) to flag where jumps are detected.

    Parameters
    ----------
    ramp_data : np.ndarray
        3D array of the UTR data with shape (Nreads, Ny, Nx).
    dq_raw : np.ndarray
        Input data quality flags for the UTR data with shape (Nreads, Ny, Nx).
    dq : np.ndarray
        Input data quality flags with shape (Ny, Nx).
    rdnoise : np.ndarray or None, optional
        Input read noise array with shape (Ny, Nx). Defaults to 0.
    gain : np.ndarray or None, optional
        Input gain array with shape (Ny, Nx). Defaults to 1.
    rejection_threshold : float, optional
        Sigma threshold for jump detection. Default is 4.0.
    max_cores : int, optional
        Maximum number of CPU cores to use for parallel processing (default: 1).
    """

    n_reads, ny, nx = ramp_data.shape

    # TODO - determine how to use the input DQ flags to ignore bad data

    if rdnoise is None:
        # TODO - optimize read noise when array is not passed
        rdnoise = np.zeros((ny, nx), dtype=np.float32)
    if gain is None:
        # TODO - optimize gain when array is not passed
        gain = np.ones((ny, nx), dtype=np.float32)

    assert n_reads >= 2, "Need at least 2 reads to do jump detection."

    with numba_thread_scope(max_cores):
        _jump_detection_difference_numba(ramp_data, dq_raw, dq, rdnoise, gain, rejection_threshold)
