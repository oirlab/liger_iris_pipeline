from ..stpipe.base_step import LigerIRISStep
from ..coadd.coadd_frames import make_frame_batch
from photutils.background import BiweightLocationBackground, Background2D
from ..utils.math import biweight_location
from astropy.stats import SigmaClip
from ..coadd.coadd_frames import coadd_frames
from .subtract_background_imager_step import subtract_background_imager

import numpy as np

import logging

logger = logging.getLogger(__name__)

__all__ = ['CalculateBackgroundImagerStep']

    
class CalculateBackgroundImagerStep(LigerIRISStep):
    """
    The background is computed from either the input science data or a dedicated background data. If several exposures are provided, the background is computed as an average of the scaled input data.

    The background is computed using `photutils.background <https://photutils.readthedocs.io/en/latest/user_guide/background.html>`_

    The appropriate master background calibration is subtracted from the input data. The input's ``err`` attribute is updated by adding the background's ``err`` attribute in quadrature. DQ flags are updated with bitwise or.

    Parameters
    ----------
    input : ImagerModel
        The input imager data model(s) to calculate the background from.
    background : ImagerModel, str, optional
        Background model to subtract.
        Default is None.
    background_output : str, optional
        Filepath to save the calculated background model.
        Default is None.
    sigma_low : float
        Number of sigma for outlier rejection.
        Default is 6.
    sigma_high : float
        Number of sigma for outlier rejection.
        Default is 2.
    maxiters : int
        Maximum number of iterations for outlier rejection.
        Default is 100.
    box_size : int
        Size of the box for background estimation.
        Default is 101.
    filter_size : int, optional
        Size of the filter for background estimation.
        Default is None.
    do_scale_calc : bool | None
        Whether to perform scaling calculations when computing background.
        Default is None.
    do_subtraction : bool
        Whether to perform background subtraction after calculating the background.
        Default is True.
    
    Returns
    -------
    output : ImagerModel
        The calculated background model.
    """

    class_alias = "background_calc"

    spec = """
        background = is_string_or_datamodel(default=None) # Background model to subtract.
        sigma_low = float(default = 6) # Number of sigma for outlier rejection.
        sigma_high = float(default = 2) # Number of sigma for outlier rejection.
        maxiters = integer(default = 100) # Maximum number of iterations for outlier rejection.
        box_size = integer(default = 101) # Size of the box for background estimation.
        filter_size = integer(default = None) # Size of the filter for background estimation.
        do_scale_calc = boolean(default=None) # Whether to perform scaling calculations when computing background.
        do_subtraction = boolean(default=True) # Whether to perform background subtraction after calculating the background.
    """

    def process(self, input):
        input_models = [self.open_model(f) for f in input]
        bkg_frames = make_frame_batch(input_models, attrs=("data", "err", "dq"))
        tel = input_models[0].meta.telescope.lower()
        if tel.startswith("keck"):
            tel_diam = 10e6
        elif tel == "tmt":
            tel_diam = 30e6
        else:
            raise ValueError(f"Unsupported telescope: {input_models[0].meta.telescope}")

        # Calculate FWHM in pixels
        fwhm = (
            1.22
            * input_models[0].meta.instrument.wave_center
            / tel_diam
            * 206265
        ) / input_models[0].meta.instrument.scale

        if len(input_models) == 1:
            do_scale_calc = 1
        elif self.do_scale_calc is not None:
            do_scale_calc = self.do_scale_calc
        else:
            do_scale_calc = True

        # Calculate the background
        logger.info("Calculating background from input image.")
        bkg_result = calc_background_imager(
            bkg_frames["data"], bkg_frames["err"], bkg_frames["dq"],
            box_size=self.box_size,
            filter_size=self.filter_size,
            sigma_clip=(self.sigma_low, self.sigma_high),
            maxiters=self.maxiters,
            fwhm=fwhm,
            do_scale_calc=do_scale_calc,
        )

        # Construct background model
        output_model_class = input_models[0].__class__
        bkg_model = output_model_class.from_datamodels(
            input_models,
            data=bkg_result['data'],
            err=bkg_result['err'],
            dq=bkg_result['dq'],
            var_rnoise=bkg_result['var_rnoise'],
            var_poisson=bkg_result['var_poisson'],
        )

        # TODO: Decide where bkg subtraction occurs
        # if self.do_subtraction:
        #     for i, model in enumerate(input_models):
        #         logger.info(f"Subtracting background from {model}.")
        #         scale = None if bkg_result['scales'] is None else bkg_result['scales'][i]
        #         subtract_background_imager(
        #             model, bkg_model,
        #             scale=scale
        #         )

        self.bkg_result = bkg_result

        return bkg_model


def calc_background_imager(
    data_frames: np.ndarray,
    err_frames: np.ndarray | None,
    dq_frames: np.ndarray,
    do_scale_calc: bool | None = None,
    box_size: tuple[int, int] | None = None,
    filter_size: tuple[int, int] | None = None,
    sigma_clip: tuple[float, float] = (6.0, 2.0),
    maxiters: int = 100,
    fwhm: float | None = None,
    do_sigma_clip: bool | None = None,
) -> dict:
    """
    Calculate background for a single image or a scaled background from a set of input frames.

    Parameters
    ----------
    data_frames : numpy.ndarray
        Image array with shape (ny, nx) or cube with shape (n_frames, ny, nx).
    err_frames : numpy.ndarray or None
        Error array with same shape as data_frames. Required if do_scale_calc is True.
    dq_frames : numpy.ndarray
        Data quality array with same shape as data_frames. Non-zero values are masked.
    do_scale_calc : bool | None
        If True, compute per-frame backgrounds, scale them, and combine.
        If False, compute background for a single image.
    do_sigma_clip : bool, optional
        Whether to perform sigma clipping during background estimation.
    box_size : tuple of int or None, optional
        Size of the box used for background estimation.
    filter_size : tuple of int or None, optional
        Size of the filter applied to the background map.
    sigma_clip : tuple of float, optional
        Lower and upper sigma-clipping thresholds.
    maxiters : int, optional
        Maximum number of sigma-clipping iterations.
    fwhm : float or None, optional
        PSF FWHM used to set box_size if box_size is None.

    Returns
    -------
    bkg_result : dict
        Background results with items:
        - 'data': 2D array of the background image.
        - 'err': 2D array of the background error.
        - 'dq': 2D array of the background data quality.
        - 'scales': 1D array of scaling factors (if do_scale_calc is True, None otherwise).
    """

    # Get box and filter sizes for smoothing
    if box_size is None:
        assert fwhm is not None, "Either box_size or fwhm must be provided."
        box_size = (int(10 * fwhm), int(10 * fwhm))
    if filter_size is None:
        filter_size = (3, 3)

    # Skip scale calculation if only one frame is provided
    n_frames, ny, nx = data_frames.shape
    if n_frames == 1 and do_scale_calc:
        logger.warning("Only one frame provided; skipping scale calculation and sigma clipping.")
        do_scale_calc = False
        do_sigma_clip = False

    # Set up background estimator and sigma clipper
    bkg_estimator = BiweightLocationBackground()
    if do_sigma_clip:
        sc = SigmaClip(
            sigma=None,
            sigma_lower=sigma_clip[0],
            sigma_upper=sigma_clip[1],
            maxiters=maxiters,
        )
    else:
        sc = None


    # Calculate background for individual frames
    backgrounds = np.zeros((n_frames, ny, nx), dtype=data_frames.dtype)
    background_rms = np.zeros((n_frames, ny, nx), dtype=data_frames.dtype)
    for i in range(n_frames):
        mask = dq_frames[i] > 0
        bkg = Background2D(
            data_frames[i],
            box_size=box_size,
            filter_size=filter_size,
            sigma_clip=sc,
            bkg_estimator=bkg_estimator,
            fill_value=np.nan,
            mask=mask,
        )
        backgrounds[i] = bkg.background
        background_rms[i] = bkg.background_rms
    
    # Compute relative scale factors and scale backgrounds if set
    if do_scale_calc:
        bkg_avgs = np.array([biweight_location(bg) for bg in backgrounds])
        bkg_ref = np.mean(bkg_avgs)
        scales = bkg_avgs / bkg_ref
        backgrounds_scaled = backgrounds / scales[:, None, None]
        background_rms_scaled = background_rms / scales[:, None, None]
    else:
        scales = None
        backgrounds_scaled = backgrounds
        background_rms_scaled = background_rms

    # Combine the scaled backgrounds
    bkg_result = coadd_frames(
        input_frames=dict(
            data=backgrounds_scaled,
            err=background_rms_scaled,
            var_rnoise=np.zeros_like(backgrounds_scaled),
            var_poisson=np.zeros_like(backgrounds_scaled),
            dq=dq_frames,
        ),
        method="mean",
        do_sigma_clip=True,
        sigma_thresh_low=4,
        sigma_thresh_high=3,
        dtype_out=backgrounds_scaled.dtype,
    )

    return dict(
        data=bkg_result['data'],
        err=bkg_result['err'],
        dq=bkg_result['dq'],
        scales=scales,
        var_rnoise=bkg_result['var_rnoise'],
        var_poisson=bkg_result['var_poisson'],
    )
