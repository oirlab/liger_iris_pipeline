from ..base_step import LigerIRISStep
from .. import datamodels
import numpy as np
from photutils.background import Background2D, BiweightLocationBackground
from astropy.stats import SigmaClip

from ..utils import math
from ..combine_frames.combine_frames_step import make_cubes, _combine_frames

__all__ = ['CalculateBackgroundImagerStep']


class CalculateBackgroundImagerStep(LigerIRISStep):
    """
    Calulate the background sky from a single frame or a group of frames with different scales.
    """

    spec = """
        sigma_low = float(default = 6) # Number of sigma for outlier rejection.
        sigma_high = float(default = 2) # Number of sigma for outlier rejection.
        maxiters = integer(default = 100) # Maximum number of iterations for outlier rejection.
        box_size = integer(default = 101) # Size of the box for background estimation.
        filter_size = integer(default = None) # Size of the box for background estimation.
    """

    class_alias = "calc_bkg_imager"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background_result = None

    def process(self, input) -> datamodels.ImagerModel:
        self.background_result = None
        if not isinstance(input, list):
            input = [input]
        background_cubes = make_cubes(input, attrs=('data', 'err', 'dq'))
        background_data_cube = background_cubes['data']
        background_dq_cube = background_cubes['dq']
        with self.open_model(input[0]) as input_model:
            if input_model.meta.telescope.lower().startswith('keck'):
                tel_diam = 10E6
            elif input_model.meta.telescope.lower() == 'tmt':
                tel_diam = 30E6
            else:
                self.log.error(f"Unsupported telescope: {input_model.meta.telescope}")
                raise ValueError(f"Unsupported telescope: {input_model.meta.telescope}")
            fwhm = (1.22 * input_model.meta.instrument.wave_center / tel_diam * 206265) / input_model.meta.instrument.scale
            sky_model = input_model.copy()
        self.log.info(f"Calculcating sky background from {input}.")
        self.background_result = calc_scaled_sky_imager(
            background_data_cube, background_dq_cube,
            box_size=self.box_size,
            filter_size=self.filter_size,
            sigma_clip=(self.sigma_low, self.sigma_high),
            maxiters=self.maxiters,
            fwhm=fwhm
        )
        sky_model.data = self.background_result['sky']
        sky_model.err = self.background_result['sky_err']
        sky_model.dq = self.background_result['sky_dq']
        self.status = "COMPLETE"
        return sky_model
    

def calc_scaled_sky_imager(
    data_cube : np.ndarray, dq_cube : np.ndarray,
    box_size : tuple[int, int] | None = None,
    filter_size : tuple[int, int] | None = None,
    sigma_clip : tuple[float, float] = (6.0, 2.0),
    maxiters : int = 100,
    fwhm : float | None = None
) -> dict:
    n_frames = data_cube.shape[0]
    sky_results = [calc_sky_imager(data_cube[i, :, :], dq_cube[i, :, :] > 0, box_size=box_size, filter_size=filter_size, sigma_clip=sigma_clip, fwhm=fwhm, maxiters=maxiters) for i in range(n_frames)]
    sky_medians = [math.biweight_location(sky.background) for sky in sky_results]
    sky_ref = np.mean(sky_medians)
    scales = sky_medians / sky_ref
    background_cube_scaled = np.array(
        [sky_results[i].background * scales[i] for i in range(n_frames)],
        dtype=data_cube.dtype
    )
    background_err_cube_scaled = np.array(
        [sky_results[i].background_rms * scales[i] for i in range(n_frames)],
        dtype=data_cube.dtype
    )
    result = _combine_frames(
        background_cube_scaled, background_err_cube_scaled, dq_cube,
        method='mean',
        do_sigma_clip=True, sigma_thresh_low=4, sigma_thresh_high=3, # NOTE: Should we still be more sensitive to upper outliers?
        dtype_out=background_cube_scaled.dtype,
    )
    return dict(
        sky=result['data'], sky_err=result['err'], sky_dq=result['dq'],
        sky_scales=scales, sky_results=sky_results
    )


def calc_sky_imager(
    image : np.ndarray, mask : np.ndarray,
    fwhm : float | None = None,
    box_size : tuple[int, int] | None = None,
    filter_size : tuple[int, int] | None = None,
    sigma_clip : tuple[float, float] = (6.0, 2.0),
    maxiters : int = 100
) -> dict:
    """
    Calculate the uniform sky level from a single image.
    
    Args:
        image (np.ndarray) : The input image data.
        mask (np.ndarray) : The input mask where 0 is 
        
    Returns:
        A dictionary containing the sky level, error, and number of pixels used.
    """
    if box_size is None:
        box_size = (int(10 * fwhm), int(10 * fwhm))
    if filter_size is None:
        filter_size = (3, 3)
    bkg_estimator = BiweightLocationBackground()
    sigma_clip = SigmaClip(sigma=None, sigma_lower=sigma_clip[0], sigma_upper=sigma_clip[1], maxiters=maxiters)
    bkg = Background2D(
        image,
        box_size=box_size, filter_size=filter_size,
        sigma_clip=sigma_clip,
        bkg_estimator=bkg_estimator,
        fill_value=np.nan,
        mask=mask,
    )
    return bkg