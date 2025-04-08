from ..base_step import LigerIRISStep
from .. import datamodels
import numpy as np
import jwst.model_blender as model_blender
from ..utils import math
from numba import njit


__all__ = ["CombineFramesStep", "combine_frames"]


class CombineFramesStep(LigerIRISStep):
    """
    CombineFramesStep: Combines a set of 2D frames.
    """

    # NOTE: Change this so that cenfunc and stdfunc govern everything(????) Add special case for sigma_clip if possible, otherwise back to thow we ar doing it currently.
    spec = """
        method = string(default = 'mean') # Method for combining the frames - 'mean', 'wmean', 'median', 'wmedian', 'sigma_clip'.
        sigma = float(default = 4) # Number of sigma for outlier rejection.
        cenfunc = string(default = 'median') # Function for calculating the center - 'mean', 'wmean', 'median', 'wmedian'.
        stdfunc = string(default = 'std') # Function for calculating the standard deviation - 'std', 'wstd', 'mad_std', 'wmad_std'.
        error_calc = string(default = 'measure') # Method for calculating the error - 'measure' or 'propagate'. Default is 'measure'.
        target_model = string(default = None) # Model type for the output. Default is the same as the input.
    """

    class_alias = "combine_frames"

    def process(self, input : list[str | datamodels.LigerIRISDataModel]):
        result = combine_frames(input, method=self.method, error_calc=self.error_calc, sigma=self.sigma, cenfunc=self.cenfunc, stdfunc=self.stdfunc)
        if self.target_model is None:
            with datamodels.open(input[0]) as model:
                target_model = model.__class__
        else:
            target_model = eval('datamodels.' + self.target_model)
        result = target_model(data=result['data'], err=result['err'], dq=result['dq'])
        model_blender.blendmodels(result, input) # TODO: Make sure individual models are stored in header
        self.status = "COMPLETE"
        return result
    

def combine_frames(
        input : list[str | datamodels.LigerIRISDataModel],
        method : str = 'mean',
        sigma : float = 4,
        cenfunc : str = 'med',
        stdfunc : str = 'std',
        error_calc : str = 'measure',
        maxiters : int = 50,
        dtype_out = None,
    ) -> dict[str, np.ndarray]:
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
    cubes = _make_cubes(input, attrs=('data', 'err', 'dq'))
    data_cube = cubes['data']
    error_cube = cubes['err']
    dq_cube = cubes['dq']
    ny, nx = data_cube.shape[0:2]
    mask_cube = dq_cube > 0
    data_cube[mask_cube] = np.nan
    weights_cube = 1 / cubes['err']**2
    weights_cube[mask_cube] = 0
    if dtype_out is None:
        dtype_out = data_cube.dtype
    if method.lower() == 'mean':
        data_out = np.nanmean(data_cube, axis=2)
    elif method.lower() == 'median':
        data_out = np.nanmedian(data_cube, axis=2)
    elif method.lower() == 'wmean':
        masked_data = np.ma.masked_array(data_cube, mask=mask_cube)
        data_out = np.ma.average(masked_data, axis=2, weights=weights_cube)
    elif method.lower() == 'wmedian':
        data_out = np.full((ny, nx), np.nan, dtype=dtype_out)
        _weighted_quantile_cube(data_cube, weights_cube, data_out, q=0.5)
    elif method.lower() == 'sigma_clip':
        # if cenfunc == 'mean':
        #     cenfunc = np.nanmean
        # elif cenfunc == 'wmean':
        #     cenfunc = math.weighted_mean(data_cube, weights_cube)
        data_out = _sigma_clip(data_cube, weights_cube=weights_cube, sigma=sigma, maxiters=maxiters, cenfunc=cenfunc, stdfunc=stdfunc)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    err_out = np.full((ny, nx), np.nan, dtype=dtype_out)
    if error_calc == 'measure':
        _meaure_error(data_out, data_cube, error_cube, dq_cube, weights_cube, err_out)
    elif error_calc == 'propagate':
        _propagate_error(data_out, data_cube, error_cube, dq_cube, weights_cube, err_out)
    else:
        raise ValueError(f"Unknown error calculation method: {error_calc}")

    dq_out = np.bitwise_and.reduce(cubes['dq'], axis=2)

    return dict(data=data_out, err=err_out, dq=dq_out)


def _make_cubes(
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
        dict[str, np.ndarray]: Dictionary of cubes with shape (Ny, Nx, Nframes).
    """
    out = {}
    n_frames = len(input)
    for i in range(n_frames):
        with datamodels.open(input[i]) as model:
            ny, nx = model.shape
            for attr in attrs:
                arr = getattr(model, attr)
                if i == 0:
                    out[attr] = np.zeros((ny, nx, n_frames), dtype=arr.dtype)
                if copy:
                    out[attr][:, :, i] = arr.copy()
                else:
                    out[attr][:, :, i] = arr
    return out


@njit(nogil=True)
def _weighted_quantile_cube(cube : np.ndarray, weights : np.ndarray, image_out : np.ndarray, q : float = 0.5):
    ny, nx = cube.shape[0:2]
    for i in range(ny):
        for j in range(nx):
            good = np.where(weights[i, j, :] > 0)[0]
            if len(good) > 0:
                image_out[i, j] = math.weighted_quantile(cube[i, j, good], weights[i, j, good], q)
    return image_out


@njit(nogil=True)
def _propagate_error(
        mean_image : np.ndarray,
        data_cube : np.ndarray, error_cube : np.ndarray, dq_cube : np.ndarray,
        weights_cube : np.ndarray,
        error_image_out : np.ndarray,
    ) -> np.ndarray:
    ny, nx = mean_image.shape
    for i in range(ny):
        for j in range(nx):
            good = np.where(dq_cube[i, j, :] == 0)[0]
            n_good = len(good)
            if n_good > 0 and np.isfinite(mean_image[i, j]):
                error_image_out[i, j] = np.sum(1 / error_cube[i, j, good]**2)**-0.5
    return error_image_out


@njit(nogil=True)
def _meaure_error(
        mean_image : np.ndarray,
        data_cube : np.ndarray, error_cube : np.ndarray, dq_cube : np.ndarray,
        weights_cube : np.ndarray,
        error_image_out : np.ndarray,
    ) -> np.ndarray:
    ny, nx = mean_image.shape
    for i in range(ny):
        for j in range(nx):
            good = np.where(dq_cube[i, j, :] == 0)[0]
            n_good = len(good)
            if n_good == 0:
                error_image_out[i, j] = np.nan
            elif n_good == 1:
                error_image_out[i, j] = error_cube[i, j, good[0]]
            else:
                error_image_out[i, j] = math.weighted_stddev(data_cube[i, j, good], weights_cube[i, j, good])
                error_image_out[i, j] /= np.sqrt(n_good - 1)
    return error_image_out


def _sigma_clip(
        data_cube : np.ndarray,
        weights_cube : np.ndarray | None = None,
        sigma : float = 4,
        maxiters : int = 50,
        cenfunc : str = 'median',
        stdfunc : str = 'mad_std'
    ) -> np.ndarray | tuple[np.ndarray, np.ndarray]:
    if weights_cube is None:
        weights_cube = np.ones_like(x)
    cenfunc = cenfunc.lower()
    stdfunc = stdfunc.lower()
    ny, nx = data_cube.shape[0:2]
    image_out = np.full((ny, nx), np.nan, dtype=data_cube.dtype)
    return _sigma_clip_median_madstd(data_cube, weights_cube, image_out, sigma, maxiters)


@njit(nogil=True)
def _sigma_clip_median_madstd(data_cube, weights_cube, image_out, sigma, maxiters):
    ny, nx, _ = data_cube.shape
    for i in range(ny):
        for j in range(nx):
            for _ in range(maxiters):
                good = np.where(weights_cube[i, j, :] > 0)[0]
                residuals = data_cube[i, j, good] - np.nanmedian(data_cube[i, j, good])
                stddev = math.mad(residuals) * 1.4826
                bad = np.where(np.abs(residuals) > sigma * stddev)[0]
                if len(bad) == 0:
                    break
                weights_cube[i, j, good[bad]] = 0
            good = np.where(weights_cube[i, j, :] > 0)[0]
            if len(good) > 0:
                image_out[i, j] = np.nanmedian(data_cube[i, j, good])
            else:
                image_out[i, j] = np.nan
    return image_out