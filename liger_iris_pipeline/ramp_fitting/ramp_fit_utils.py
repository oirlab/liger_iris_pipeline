import numpy as np
from ..datamodels.dqflags import DQ_FLAGS
from numba import njit, prange

SATURATED_FLAG_uint8 = np.uint8(DQ_FLAGS["SATURATED"])
DO_NOT_USE_FLAG_uint8 = np.uint8(DQ_FLAGS["DO_NOT_USE"])
JUMP_DET_FLAG_uint8 = np.uint8(DQ_FLAGS["JUMP_DET"])

@njit(inline="always")
def mean_numba_if_not_zero(arr: np.ndarray) -> float:
    total = 0.0
    n = 0
    for i in range(arr.size):
        if arr[i] != 0:
            total += arr[i]
            n = n + 1
    if n != 0:
        return total / n
    else:
        return 0

@njit(nogil=True, cache=True)
def get_mid_delta_times_ramp(times: np.ndarray, dq_raw: np.ndarray) -> float:
    """
    Compute the mid time of the exposure accounting for the DQ flags: DO_NOT_USE, SATURATED, or JUMP_DET.

    Parameters
    ----------
    times : np.ndarray
        1D array of read times (length n_reads).
    dq_raw : np.ndarray uint8
        1D array of data quality flags (length n_reads).

    Returns
    -------
    mid_delta_time : float
        The average mid time of the valid exposures, or NaN if no valid exposures exist.
    """
    n_reads = len(times)
    avg_bin_times = (times[0:n_reads - 1] + times[1::]) / 2

    mask = ((dq_raw & DO_NOT_USE_FLAG_uint8) | (dq_raw & SATURATED_FLAG_uint8)).astype(np.bool)
    mask2 = (dq_raw & JUMP_DET_FLAG_uint8).astype(np.bool)
    avg_bin_times = avg_bin_times * ~(mask[1:n_reads] | mask[0:n_reads - 1] | mask2[1:n_reads])

    mid_delta_time = mean_numba_if_not_zero(avg_bin_times)
    return mid_delta_time


@njit(nogil=True, cache=True)
def get_ramp_chunks(dq_raw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Returns (starts, ends) arrays of indices of dtype int64.
    Drops everything at and after the first SATURATED index.
    Keeps the JUMP_DET read but splits before it (i.e., previous chunk ends at i-1,
    next chunk starts at i).
    Excludes DO_NOT_USE reads entirely (may split).

    Notes
    -----
    Does NOT filter out single-read chunks; wrapper does that.

    Parameters
    ----------
    dq_raw : np.ndarray uint8
        1D array of data quality flags (length n_reads).
    
    Returns
    -------
    starts : np.ndarray int32
        1D array of starting indices of valid ramp chunks.
    ends : np.ndarray int32
        1D array of ending indices (exclusive) of valid ramp chunks.
    """
    n = dq_raw.size

    # Find first saturated index; exclude it and everything after.
    n_use = 1
    for i in range(n):
        # checking backward for saturation to speed up processing since saturation will be at the end of the ramp
        if (dq_raw[n-i-1] & (SATURATED_FLAG_uint8 | DO_NOT_USE_FLAG_uint8)) == 0:
            n_use = n-i
            break
    #If all bad, n_use will be 1, and we return empty arrays below
    #If no trailing bad reads, then n_use == n
    if n_use == 1:
        return np.empty(0, dtype=np.int32), np.empty(0, dtype=np.int32)

    # Preallocate worst-case space (each valid run -> separate chunk)
    starts = np.empty(n_use//2+1, dtype=np.int32)
    ends = np.empty(n_use//2+1, dtype=np.int32)
    count = 0

    in_chunk = False
    start = 0

    for i in range(n_use):
        dqv = dq_raw[i]

        # If bad, close chunk and move to next read
        if (dqv & DO_NOT_USE_FLAG_uint8) != 0:
            if in_chunk: # then close chunk
                end = i
                if end - start >= 2:
                    starts[count] = start
                    ends[count]   = end
                    count += 1
                in_chunk = False
            continue

        # If jump, close chunk and start new one
        if (dqv & JUMP_DET_FLAG_uint8) != 0:
            if in_chunk: # then close chunk
                end = i
                if end - start >= 2:
                    starts[count] = start
                    ends[count]   = end
                    count += 1
                in_chunk = False

        # Open chunk if needed
        if not in_chunk:
            start = i
            in_chunk = True

    # Flush trailing chunk
    if in_chunk:
        end = n_use
        if end - start >= 2:
            starts[count] = start
            ends[count]   = end
            count += 1

    return starts[:count], ends[:count]

@njit(nogil=True, parallel=True, cache=True)
def get_mid_delta_times(times: np.ndarray, dq_raw: np.ndarray) -> np.ndarray:
    """
    Parallelized wrapper for get_mid_delta_times_ramp to apply on a 3D DQ array.
    Loops over the 2nd and 3rd dimensions (y, x) and applies get_mid_delta_times to each pixel.

    Parameters
    ----------
    times : np.ndarray
        1D array of read times (length N_reads).
    dq_raw : np.ndarray
        3D array of DQ flags uint8 with shape (N_reads, Ny, Nx).

    Returns
    -------
    mid_time_map : np.ndarray
        2D array (Ny, Nx) of mid times for each pixel.
    """
    n_reads, ny, nx = dq_raw.shape
    mid_time_map = np.empty((ny, nx), dtype=np.float32)
    for j in prange(ny):
        for k in range(nx):
            mid_time_map[j, k] = get_mid_delta_times_ramp(times, dq_raw[:, j, k])
    return mid_time_map

@njit(inline="always")
def bitwise_or_reduce(arr: np.ndarray) -> np.uint8:
    result = np.uint8(0)
    for k in range(arr.shape[0]):
        result |= arr[k]
    return result