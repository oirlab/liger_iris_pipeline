import numpy as np
from numba import njit
from .sigma_clipping import sigma_clip_frames

from .. import datamodels
from ..datamodels import LigerIRISDataModel
from ..utils.math import weighted_mean, weighted_quantile
from ..utils.errors import propagate_error, measure_error, propagate_variance

def coadd_frames(
    input_frames : dict[str, np.ndarray],
    method : str = 'mean',
    do_sigma_clip : bool = True,
    sigma_thresh_low : float | None = None, sigma_thresh_high : float | None = None,
    thresh_low : float | None = None, thresh_high : float = None,
    num_mask_low : int | None = None, num_mask_high : int | None = None,
    min_batch_size : int = 3,
    maxiters : int = 50,
    error_calc : str = 'propagate',
    dtype_out = None,
    dq_reduce : str = 'and',
) -> dict[str, np.ndarray]:
    """
    Combine a stack of 2D frames.

    Parameters
    ----------
    input_frames : dict[str, np.ndarray]
        Dictionary of input frames to coadd with keys:
            - 'data' : 3D array of data frames to coadd with shape (Nframes, Ny, Nx).
            - 'err' : 3D array of error frames to coadd with shape (Nframes, Ny, Nx).
            - 'var_rnoise' : 3D array of read noise variance frames to coadd with shape (Nframes, Ny, Nx).
            - 'var_poisson' : 3D array of Poisson noise variance frames to coadd with shape (Nframes, Ny, Nx).
            - 'mask' or 'dq' : 3D array of data quality (dq) or mask frames to coadd with shape (Nframes, Ny, Nx).
                If 'dq' is provided, it will be used as a mask where dq == 0.
                If 'mask' is provided, 1 indicates good and 0 indicates bad.
                If both are provided, the mask is updated according to where dq == 0.

    method : str, optional
        Method for combining frames. Options are 'mean', 'median', 'wmean', 'wmedian'.
    do_sigma_clip : bool, optional
        Whether to perform sigma clipping before combining frames.
    sigma_thresh_low : float | None, optional
        Low sigma threshold for sigma clipping.
    sigma_thresh_high : float | None, optional
        High sigma threshold for sigma clipping.
    thresh_low : float | None, optional
        Low threshold for sigma clipping.
    thresh_high : float | None, optional
        High threshold for sigma clipping.
    num_mask_low : int | None, optional
        Number of low outliers to mask.
    num_mask_high : int | None, optional
        Number of high outliers to mask.
    min_batch_size : int, optional
        Minimum batch size for sigma clipping.
    maxiters : int, optional
        Maximum number of iterations for sigma clipping.
    error_calc : str, optional
        Method for calculating the error. Options are 'measure' or 'propagate'.
    dtype_out : data-type, optional
        Desired data type for output arrays. Default is None, which uses input data type.
    dq_reduce : str, optional
        Method for reducing DQ flags. Options are 'and' or 'or'.

    Returns
    -------
    dict
        Dictionary of coadded frames with keys:
            - 'data' : 2D array of coadded data frame with shape (Ny, Nx).
            - 'err' : 2D array of coadded error frame with shape (Ny, Nx).
            - 'var_rnoise' : 2D array of coadded read noise variance frame with shape (Ny, Nx).
            - 'var_poisson' : 2D array of coadded Poisson noise variance frame with shape (Ny, Nx).
            - 'mask' : The updated 3D mask array (1 = good, 0 = bad) with shape (Nframes, Ny, Nx).
            - 'dq' : 2D array of coadded DQ frame with shape (Ny, Nx).
    """

    # Data
    data_frames = input_frames['data']

    # Mask
    mask = np.isfinite(data_frames)
    if 'mask' in input_frames:
        mask &= input_frames['mask'].astype(bool)

    if 'dq' in input_frames:
        dq_frames = input_frames['dq']
        mask &= dq_frames == 0

    # Weights from error
    if 'err' in input_frames:
        error_frames = input_frames['err']
        weights = 1 / error_frames**2
    else:
        weights = np.ones_like(data_frames)

    # Set weights to 0 where mask is True
    weights[~mask] = 0

    # Get output data type
    if dtype_out is None:
        dtype_out = data_frames.dtype

    # Check if we do sigma clipping
    if do_sigma_clip:
        sigma_clip_frames(
            data_frames, mask,
            sigma_thresh_low=sigma_thresh_low, sigma_thresh_high=sigma_thresh_high,
            thresh_low=thresh_low, thresh_high=thresh_high,
            num_mask_low=num_mask_low, num_mask_high=num_mask_high,
            min_batch_size=min_batch_size,
            maxiters=maxiters,
        )
        weights[~mask] = 0

    # Final reduction
    method = method.lower()
    if method == 'mean':
        data_out = np.nanmean(np.where(mask, data_frames, np.nan), axis=0)
    elif method == 'median':
        data_out = np.nanmedian(np.where(mask, data_frames, np.nan), axis=0)
    elif method == 'wmean':
        data_out = np.zeros(data_frames.shape[1:], dtype=dtype_out)
        weighted_mean_frames(data_frames, weights, data_out)
    elif method == 'wmedian':
        data_out = np.zeros(data_frames.shape[1:], dtype=dtype_out)
        weighted_quantile_frames(data_frames, weights, data_out, q=0.5)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Calulate the error
    if 'err' in input_frames:
        if error_calc == 'measure':
            err_out = measure_error_frames(data_frames, error_frames, mask)
        elif error_calc == 'propagate':
            err_out = propagate_error_frames(error_frames, mask)
        else:
            raise ValueError(f"Unknown error calculation method: {error_calc}")
    else:
        err_out = None
    
    # Always propagate var rnoise and var poisson
    if 'var_rnoise' in input_frames:
        var_rnoise_out = propagate_variance_frames(input_frames['var_rnoise'], mask)
    else:
        var_rnoise_out = None

    if 'var_poisson' in input_frames:
        var_poisson_out = propagate_variance_frames(input_frames['var_poisson'], mask)
    else:
        var_poisson_out = None

    # Reduce the DQ flags
    if 'dq' in input_frames:
        if dq_reduce.lower() == 'or':
            dq_out = np.bitwise_or.reduce(dq_frames, axis=0)
        elif dq_reduce.lower() == 'and':
            dq_out = np.bitwise_and.reduce(dq_frames, axis=0)
        else:
            raise ValueError(f"Unknown DQ reduction method: {dq_reduce}")
        
    else:
        dq_out = None

    return dict(
        data=data_out,
        err=err_out,
        var_rnoise=var_rnoise_out,
        var_poisson=var_poisson_out,
        mask=mask,
        dq=dq_out
    )

def make_frame_batch(
    input : list[str | LigerIRISDataModel],
    attrs : tuple[str],
) -> dict[str, np.ndarray]:
    out = {}
    n_frames = len(input)
    for i in range(n_frames):
        with datamodels.open(input[i]) as model:
            ny, nx = model.shape
            for attr in attrs:
                arr = getattr(model, attr)
                if i == 0:
                    out[attr] = np.zeros((n_frames, ny, nx), dtype=arr.dtype)
                out[attr][i, :, :] = arr
    return out

@njit(nogil=True)
def weighted_quantile_frames(
    data_frames : np.ndarray, weights : np.ndarray,
    image_out : np.ndarray,
    q : float = 0.5
) -> np.ndarray:
    ny, nx = data_frames.shape[1:]
    for i in range(ny):
        for j in range(nx):
            good = np.where(np.isfinite(weights[:, i, j]) & (weights[:, i, j] > 0))[0]
            if len(good) > 0:
                image_out[i, j] = weighted_quantile(data_frames[good, i, j], weights[good, i, j], q)

@njit(nogil=True)
def weighted_mean_frames(
    data_frames : np.ndarray, weights : np.ndarray,
    image_out : np.ndarray,
) -> np.ndarray:
    ny, nx = data_frames.shape[1:]
    for i in range(ny):
        for j in range(nx):
            good = np.where(np.isfinite(weights[:, i, j]) & (weights[:, i, j] > 0))[0]
            if len(good) > 0:
                image_out[i, j] = weighted_mean(data_frames[good, i, j], weights[good, i, j])

@njit(nogil=True)
def propagate_error_frames(error_frames : np.ndarray, mask : np.ndarray) -> np.ndarray:
    _, ny, nx = error_frames.shape
    out = np.zeros((ny, nx), dtype=error_frames.dtype)
    for i in range(ny):
        for j in range(nx):
            out[i, j] = propagate_error(error_frames[:, i, j], mask[:, i, j])
    return out

@njit(nogil=True)
def propagate_variance_frames(variance_frames : np.ndarray, mask : np.ndarray) -> np.ndarray:
    _, ny, nx = variance_frames.shape
    out = np.zeros((ny, nx), dtype=variance_frames.dtype)
    for i in range(ny):
        for j in range(nx):
            out[i, j] = propagate_variance(variance_frames[:, i, j], mask[:, i, j])
    return out

@njit(nogil=True)
def measure_error_frames(
    data_frames : np.ndarray, error_frames : np.ndarray, mask : np.ndarray,
) -> np.ndarray:
    _, ny, nx = error_frames.shape
    out = np.zeros((ny, nx), dtype=error_frames.dtype)
    for i in range(ny):
        for j in range(nx):
            out[i, j] = measure_error(data_frames[:, i, j], error_frames[:, i, j], mask[:, i, j])
    return out