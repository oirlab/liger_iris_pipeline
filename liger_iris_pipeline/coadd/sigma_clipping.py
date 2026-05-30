import numpy as np
from ..utils import math
from numba import njit

@njit(nogil=True)
def sigma_clip_frames(
    data_frames : np.ndarray, mask_frames : np.ndarray,
    sigma_thresh_low : float | None = None, sigma_thresh_high : float | None = None,
    thresh_low : float | None = None, thresh_high : float = None,
    num_mask_low : int | None = None, num_mask_high : int | None = None,
    min_batch_size : int = 3,
    maxiters : int = 50,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Perform sigma clipping on a stack of frames.
    mask_frames is updated in-place with outliers set to ``False``.

    Parameters
    ----------
    data_frames : np.ndarray
        3D array of data frames to sigma clip with shape (Nframes, Ny, Nx).
    mask_frames : np.ndarray
        3D array of boolean mask frames with shape (Nframes, Ny, Nx).
        True indicates "good", False indicates "bad".
        Sigma clipping will only be performed on "good" pixels as indicated by the mask.
        Flagged pixels will be set to False in the output mask.
    sigma_thresh_low : float | None, optional
        Low sigma threshold for sigma clipping.
    sigma_thresh_high : float | None, optional
        High sigma threshold for sigma clipping.
    thresh_low : float | None, optional
        Low threshold for sigma clipping.
    thresh_high : float | None, optional
        High threshold for sigma clipping.
    num_mask_low : int | None, optional
        Maximum number of low outliers to mask. If None, no limit is applied.
    num_mask_high : int | None, optional
        Maximum number of high outliers to mask. If None, no limit is applied.
    min_batch_size : int, optional
        Minimum number of unmasked pixels required to perform sigma clipping. Default is 3.
    maxiters : int, optional
        Maximum number of iterations for sigma clipping. Default is 50.

    """
    ny, nx = data_frames.shape[1:]
    for i in range(ny):
        for j in range(nx):
            mask = mask_frames[:, i, j]
            if math.any_sc(mask):
                _mask_out, _, _, _ = sigma_clip(
                    data_frames[:, i, j], mask,
                    sigma_thresh_low=sigma_thresh_low, sigma_thresh_high=sigma_thresh_high,
                    thresh_low=thresh_low, thresh_high=thresh_high,
                    num_mask_low=num_mask_low, num_mask_high=num_mask_high,
                    min_batch_size=min_batch_size,
                    maxiters=maxiters,
                )
                mask_frames[:, i, j] = _mask_out

@njit(nogil=True)
def sigma_clip(
    x: np.ndarray, mask: np.ndarray,
    sigma_thresh_low: float | None = None, sigma_thresh_high: float | None = None,
    thresh_low: float | None = None, thresh_high: float = None,
    num_mask_low: int | None = None, num_mask_high: int | None = None,
    min_batch_size: int = 3,
    maxiters: int = 50,
) -> tuple[np.ndarray, float, float, int]:
    """
    Perform sigma clipping on an input array.

    Parameters
    ----------
    x : np.ndarray
        Input array of data values to sigma clip.
    mask : np.ndarray
        Boolean array of the same shape as x where True indicates "good" and False indicates "bad".
    sigma_thresh_low : float | None, optional
        Low sigma threshold for sigma clipping. If None, no low sigma clipping is performed.
    sigma_thresh_high : float | None, optional
        High sigma threshold for sigma clipping. If None, no high sigma clipping is performed.
    thresh_low : float | None, optional
        Low threshold for sigma clipping. If None, no low threshold clipping is performed.
    thresh_high : float | None, optional
        High threshold for sigma clipping. If None, no high threshold clipping is performed.
    num_mask_low : int | None, optional
        Maximum number of low outliers to mask. If None, no limit is applied.
    num_mask_high : int | None, optional
        Maximum number of high outliers to mask. If None, no limit is applied.
    min_batch_size : int, optional
        Minimum number of unmasked pixels required to perform sigma clipping. Default is 3.
    maxiters : int, optional
        Maximum number of iterations for sigma clipping. Default is 50.

    Returns
    -------
    tuple[np.ndarray, float, float, int]
        Tuple of (mask_out, center, stddev, n_iters) where:
            - mask_out : boolean array of the same shape as input mask with outliers masked as False.
            - center : float, the biweight location of the input data.
            - stddev : float, the biweight midvariance (standard deviation) of the input data.
            - n_iters : int, number of iterations performed.
    """

    input_shape = x.shape
    x = x.ravel()
    mask = mask.ravel().copy() # Do not modify input mask

    center = np.nan
    stddev = np.nan

    for i in range(maxiters):
        x_masked = x[mask]  # select only unmasked values
        if len(x_masked) <= min_batch_size:
            break

        center = math.biweight_location(x_masked)
        var = math.biweight_midvariance(x_masked, center=center)
        stddev = np.sqrt(var)

        n_good = np.sum(mask)
        mask_outliers(
            x, center, stddev, mask,
            sigma_thresh_low=sigma_thresh_low, sigma_thresh_high=sigma_thresh_high,
            thresh_low=thresh_low, thresh_high=thresh_high,
            num_mask_low=num_mask_low, num_mask_high=num_mask_high,
        )
        n_good_new = np.sum(mask)
        if n_good_new == n_good:
            break

    # Total number of iterations used
    iters_out = i + 1

    # Reshape mask out back to original shape
    mask_out = mask.reshape(input_shape)

    return mask_out, center, stddev, iters_out


@njit(nogil=True)
def mask_outliers(
    x : np.ndarray,
    center : float, stddev : float,
    mask : np.ndarray,
    sigma_thresh_low : float | None = None, sigma_thresh_high : float | None = None,
    thresh_low : float | None = None, thresh_high : float = None,
    num_mask_low : int | None = None, num_mask_high : int | None = None,
) -> np.ndarray:
    """
    Mask outliers in a dataset based on specified thresholds.
    
    Parameters
    ----------
    x : np.ndarray
        1D array of data values.
    center : float
        Central location (e.g. mean or median) of the data.
    stddev : float
        Standard deviation of the data.
    mask : np.ndarray
        1D data mask where 0 is bad, 1 is good.
    sigma_thresh_low : float | None, optional
        Low sigma threshold for outlier rejection. If None, no low sigma clipping is performed.
    sigma_thresh_high : float | None, optional
        High sigma threshold for outlier rejection. If None, no high sigma clipping is performed.
    thresh_low : float | None, optional
        Low threshold for outlier rejection. If None, no low threshold clipping is performed.
    thresh_high : float | None, optional
        High threshold for outlier rejection. If None, no high threshold clipping is performed.
    num_mask_low : int | None, optional
        Maximum number of low outliers to mask. If None, no limit is applied.
    num_mask_high : int | None, optional
        Maximum number of high outliers to mask. If None, no limit is applied.

    Returns
    -------
    mask_out : np.ndarray
        Mask is updated in-place and returned.
    """
    res = (x - center).ravel()
    mask = mask.ravel()
    n = len(res)
    masked_low = 0
    masked_high = 0
    for i in range(n):
        if not mask[i]:
            continue

        candidate_low = False
        candidate_high = False

        if sigma_thresh_low is not None and res[i] < -sigma_thresh_low * stddev:
            candidate_low = True
        if thresh_low is not None and res[i] < thresh_low:
            candidate_low = True

        if sigma_thresh_high is not None and res[i] > sigma_thresh_high * stddev:
            candidate_high = True
        if thresh_high is not None and res[i] > thresh_high:
            candidate_high = True

        # Apply low-side masking
        if candidate_low:
            if num_mask_low is None or masked_low < num_mask_low:
                mask[i] = 0
                masked_low += 1

        # Apply high-side masking
        elif candidate_high:
            if num_mask_high is None or masked_high < num_mask_high:
                mask[i] = 0
                masked_high += 1

    return mask