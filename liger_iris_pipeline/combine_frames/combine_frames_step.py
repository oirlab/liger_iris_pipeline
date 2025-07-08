from ..base_step import LigerIRISStep
from .. import datamodels
import numpy as np
import jwst.model_blender as model_blender
from ..utils import math
from numba import njit
from ..utils.errors import measure_error, propagate_error
from ..utils.endian_utils import normalize_dtype_array


__all__ = ["CombineFramesStep", "combine_frames"]


class CombineFramesStep(LigerIRISStep):
    """
    CombineFramesStep: Combines a set of 2D frames.
    """

    # NOTE: Change this so that cenfunc and stdfunc govern everything(????) Add special case for sigma_clip if possible, otherwise back to thow we ar doing it currently.
    spec = """
        method = string(default = 'mean') # Method for combining the frames - 'mean', 'wmean', 'median', 'wmedian'.
        do_sigma_clip = boolean(default = True) # Whether to do sigma clipping. Sigma clipping is based on the biweight location and biweight midvariance (both unweighted), regardless of the 'method' parameter.
        sigma_thresh_low = float(default = 4) # Number of sigma for low outlier rejection.
        sigma_thresh_high = float(default = 4) # Number of sigma for high outlier rejection.
        thresh_low = float(default = None) # Low threshold for outlier rejection.
        thresh_high = float(default = None) # High threshold for outlier rejection.
        num_mask_low = integer(default = None) # Number of low outliers to mask.
        num_mask_high = integer(default = None) # Number of high outliers to mask.
        min_batch_size = integer(default = 3) # Minimum batch size for sigma clipping.
        maxiters = integer(default = 50) # Maximum number of iterations for sigma clipping.
        error_calc = string(default = 'measure') # Method for calculating the error - 'measure' or 'propagate'. Default is 'measure'.
        target_model = string(default = None) # Model type for the output. Default is the same as the input.
    """

    class_alias = "combine_frames"

    def process(self, input : list[str | datamodels.LigerIRISDataModel]):
        result = combine_frames(
            input,
            method=self.method, error_calc=self.error_calc,
            sigma_thresh_low=self.sigma_thresh_low, sigma_thresh_high=self.sigma_thresh_high,
            thresh_low=self.thresh_low, thresh_high=self.thresh_high,
            num_mask_low=self.num_mask_low, num_mask_high=self.num_mask_high,
            min_batch_size=self.min_batch_size,
            maxiters=self.maxiters,
            do_sigma_clip=self.do_sigma_clip,
            dq_reduce='or'
        )
        if self.target_model is None:
            with datamodels.open(input[0]) as model:
                target_model = model.__class__
        else:
            if isinstance(self.target_model, str):
                target_model = eval('datamodels.' + self.target_model)
            else:
                target_model = self.target_model
        result = target_model(data=result['data'], err=result['err'], dq=result['dq'])
        model_blender.blendmodels(result, input) # TODO: Make sure individual models are stored in header
        self.status = "COMPLETE"
        return result
    

def combine_frames(input : list[str | datamodels.LigerIRISDataModel], **kwargs) -> dict[str, np.ndarray]:
    """
    Combine a stack of 2D frames.

    Args:
        input (list[str | datamodels.LigerIRISDataModel]): List of input frames to combine.
        method (str): Method to use for combining the frames:
            - 'mean' : Unweighted mean.
            - 'wmean' : Weighted mean.
            - 'median' : Unweighted median.
            - 'wmedian' : Weighted median.
            - 'sigma_clip' : Sigma clipping (see `cenfunc`, `stdfunc`, and `sigma`).
        sigma (float) : Number of sigmas for sigma-clipping.
        cenfunc (str): Function to use for calculating the center of the data:
            - 'mean' : Unweighted mean.
            - 'wmean' : Weighted mean.
            - 'median' : Unweighted median.
            - 'wmedian' : Weighted median.

        error_calc (str): Method to use for calculating the error ('measure' or 'propagate').
            - 'measure' : Error is calcualted from the distribution (stddev) of the data relative to the final mean.
            - 'propagate' : Error is calculated by coadding the individual errors.
            Default is 'measure'.

    Returns:
        dict: Dictionary of combined frames.
    """
    cubes = make_cubes(input, attrs=('data', 'err', 'dq'))
    data_cube = cubes['data']
    error_cube = cubes['err']
    dq_cube = cubes['dq']
    return _combine_frames(data_cube, error_cube, dq_cube, **kwargs)


def _combine_frames(
    data_cube : np.ndarray,
    error_cube : np.ndarray,
    dq_cube : np.ndarray,
    method : str = 'mean',
    do_sigma_clip : bool = True,
    sigma_thresh_low : float | None = None, sigma_thresh_high : float | None = None,
    thresh_low : float | None = None, thresh_high : float = None,
    num_mask_low : int | None = None, num_mask_high : int | None = None,
    min_batch_size : int = 3,
    maxiters : int = 50,
    error_calc : str = 'measure',
    dtype_out = None,
    dq_reduce : str = 'and',
) -> dict[str, np.ndarray]:
    """
    Combine a stack of 2D frames.

    Args:
        input (list[str | datamodels.LigerIRISDataModel]): List of input frames to combine.
        do_sigma_clip (bool): Whether to do sigma clipping.
            Sigma clipping is based on the biweight location and biweight midvariance (both unweighted).

        method (str): Method to use for combining the frames:
            - 'mean' : Unweighted mean.
            - 'wmean' : Weighted mean.
            - 'median' : Unweighted median.
            - 'wmedian' : Weighted median.
        sigma (float) : Number of sigmas for sigma-clipping.
            - 'mean' : Unweighted mean.
            - 'wmean' : Weighted mean.
            - 'median' : Unweighted median.
            - 'wmedian' : Weighted median.

        error_calc (str): Method to use for calculating the error ('measure' or 'propagate').
            - 'measure' : Error is calcualted from the distribution (stddev) of the data relative to the final mean.
            - 'propagate' : Error is calculated by coadding the individual errors.
            Default is 'measure'.

    Returns:
        dict: Dictionary of combined frames.
    """

    # Get weights and mask bad pixels
    mask_cube = dq_cube > 0
    weights_cube = 1 / error_cube**2
    weights_cube[mask_cube] = 0 # Set weights to 0 where mask is True

    # Get output data type
    if dtype_out is None:
        dtype_out = data_cube.dtype

    # Check if we do sigma clipping
    if do_sigma_clip:
        sigma_clip_cube(
            data_cube, mask_cube,
            sigma_thresh_low=sigma_thresh_low, sigma_thresh_high=sigma_thresh_high,
            thresh_low=thresh_low, thresh_high=thresh_high,
            num_mask_low=num_mask_low, num_mask_high=num_mask_high,
            min_batch_size=min_batch_size,
            maxiters=maxiters,
        )
        weights_cube[mask_cube] = 0
        data_cube[mask_cube] = np.nan

    # Run the requeted method
    method = method.lower()
    if method == 'mean':
        data_out = np.nanmean(data_cube, axis=0)
    elif method == 'median':
        data_out = np.nanmedian(data_cube, axis=0)
    elif method == 'wmean':
        masked_data = np.ma.masked_array(data_cube, mask=mask_cube)
        data_out = np.ma.average(masked_data, axis=0, weights=weights_cube)
    elif method == 'wmedian':
        data_out = weighted_quantile_cube(data_cube, weights_cube, q=0.5)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Calulate the error
    if error_calc == 'measure':
        err_out = meaure_error_cube(data_cube, error_cube, dq_cube)
    elif error_calc == 'propagate':
        err_out = propagate_error_cube(error_cube, dq_cube)
    else:
        raise ValueError(f"Unknown error calculation method: {error_calc}")

    # Reduce the DQ flags
    if dq_reduce.lower() == 'or':
        dq_out = np.bitwise_or.reduce(dq_cube, axis=0)
    elif dq_reduce.lower() == 'and':
        dq_out = np.bitwise_and.reduce(dq_cube, axis=0)
    else:
        raise ValueError(f"Unknown DQ reduction method: {dq_reduce}")

    return dict(data=data_out, err=err_out, dq=dq_out)


def make_cubes(
    input : list[str | datamodels.LigerIRISDataModel],
    attrs : tuple[str],
    copy : bool = True
) -> dict[str, np.ndarray]:
    """
    Create a cube from a list of input frames.

    Args:
        input (list[str | datamodels.LigerIRISDataModel]): List of input frames to combine.
        attrs (tuple[str]): List of attributes to extract from the input frames.

    Returns:
        dict[str, np.ndarray]: Dictionary of cubes with shape (Nframes, Ny, Nx).
    """
    out = {}
    n_frames = len(input)
    for i in range(n_frames):
        with datamodels.open(input[i]) as model:
            ny, nx = model.shape
            for attr in attrs:
                arr = getattr(model, attr)
                if i == 0:
                    out[attr] = np.zeros((n_frames, ny, nx), dtype=arr.dtype)
                if copy and isinstance(input[i], datamodels.LigerIRISDataModel):
                    out[attr][i, :, :] = arr.copy()
                else:
                    out[attr][i, :, :] = arr
    for attr in attrs:
        out[attr] = normalize_dtype_array(out[attr])
    return out


@njit(nogil=True)
def weighted_quantile_cube(cube : np.ndarray, weights : np.ndarray, image_out : np.ndarray, q : float = 0.5):
    ny, nx = cube.shape[1:]
    image_out = np.full((ny, nx), np.nan, dtype=cube.dtype)
    for i in range(ny):
        for j in range(nx):
            good = np.where(weights[:, i, j] > 0)[0]
            if len(good) > 0:
                image_out[i, j] = math.weighted_quantile(cube[good, i, j], weights[good, i, j], q)
    return image_out


@njit(nogil=True)
def propagate_error_cube(
    error_cube : np.ndarray,
    dq_cube : np.ndarray,
) -> np.ndarray:
    _, ny, nx = error_cube.shape
    error_image_out = np.full((ny, nx), np.nan, dtype=error_cube.dtype)
    for i in range(ny):
        for j in range(nx):
            error_image_out[i, j] = propagate_error(error_cube[:, i, j], dq_cube[:, i, j])
    return error_image_out


@njit(nogil=True)
def meaure_error_cube(
    data_cube : np.ndarray, error_cube : np.ndarray, dq_cube : np.ndarray,
) -> np.ndarray:
    _, ny, nx = error_cube.shape
    error_image_out = np.full((ny, nx), np.nan, dtype=error_cube.dtype)
    for i in range(ny):
        for j in range(nx):
            error_image_out[i, j] = measure_error(data_cube[:, i, j], error_cube[:, i, j], dq_cube[:, i, j])
    return error_image_out


@njit(nogil=True)
def sigma_clip_cube(
    data_cube : np.ndarray, mask_cube : np.ndarray,
    sigma_thresh_low : float | None = None, sigma_thresh_high : float | None = None,
    thresh_low : float | None = None, thresh_high : float = None,
    num_mask_low : int | None = None, num_mask_high : int | None = None,
    min_batch_size : int = 3,
    maxiters : int = 50,
) -> tuple[np.ndarray, np.ndarray]:
    ny, nx = data_cube.shape[1:]
    for i in range(ny):
        for j in range(nx):
            mask = mask_cube[:, i, j]
            if not math.all_sc(mask):
                _mask_out, _, _, _ = sigma_clip(
                    data_cube[:, i, j], mask,
                    sigma_thresh_low=sigma_thresh_low, sigma_thresh_high=sigma_thresh_high,
                    thresh_low=thresh_low, thresh_high=thresh_high,
                    num_mask_low=num_mask_low, num_mask_high=num_mask_high,
                    min_batch_size=min_batch_size,
                    maxiters=maxiters,
                )
                mask_cube[:, i, j] = _mask_out

@njit(nogil=True)
def sigma_clip(
    x: np.ndarray, mask: np.ndarray,
    sigma_thresh_low: float | None = None, sigma_thresh_high: float | None = None,
    thresh_low: float | None = None, thresh_high: float = None,
    num_mask_low: int | None = None, num_mask_high: int | None = None,
    min_batch_size: int = 3,
    maxiters: int = 50,
) -> tuple[np.ndarray, float, float, int]:

    input_shape = x.shape
    x = x.ravel()
    mask = mask.ravel().copy()  # avoid modifying input mask

    for i in range(maxiters):
        x_masked = x[~mask]  # select only unmasked values
        if len(x_masked) <= min_batch_size:
            break

        M = math.biweight_location(x_masked)
        var = math.biweight_midvariance(x_masked, M=M)
        stddev = np.sqrt(var)

        n_good = np.sum(~mask)
        mask = mask_outliers(
            x, M, stddev, mask,
            sigma_thresh_low=sigma_thresh_low, sigma_thresh_high=sigma_thresh_high,
            thresh_low=thresh_low, thresh_high=thresh_high,
            num_mask_low=num_mask_low, num_mask_high=num_mask_high,
        )
        n_good_new = np.sum(~mask)
        if n_good_new == n_good:
            break

    return mask.reshape(input_shape), M, stddev, i + 1


@njit(nogil=True)
def mask_outliers(
    x : np.ndarray,
    M : float, stddev : float,
    mask : np.ndarray,
    sigma_thresh_low : float | None = None, sigma_thresh_high : float | None = None,
    thresh_low : float | None = None, thresh_high : float = None,
    num_mask_low : int | None = None, num_mask_high : int | None = None,
) -> np.ndarray:
    res = (x - M).ravel()
    mask = mask.ravel()
    n = len(res)
    masked_low = 0
    masked_high = 0
    #import matplotlib.pyplot as plt
    for i in range(n):
        if mask[i]:
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
                mask[i] = True
                masked_low += 1

        # Apply high-side masking
        elif candidate_high:
            if num_mask_high is None or masked_high < num_mask_high:
                mask[i] = True
                masked_high += 1

    return mask