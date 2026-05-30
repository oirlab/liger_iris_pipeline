from ..stpipe.base_step import LigerIRISStep
from .. import datamodels
from .coadd_frames import coadd_frames, make_frame_batch


__all__ = ["CoaddFramesStep"]


class CoaddFramesStep(LigerIRISStep):
    """
    Coadds multiple input frames to create a higher signal-to-noise output frame.

    TODO: Add parallelization.

    Parameters
    ----------
    input : Sequence of LigerIRISDataModels
        The input frames to coadd. Arrays must be 2D.
    method : str
        Method for combining the frames - 'mean', 'wmean', 'median', 'wmedian'.
        Default is 'wmean'.
    do_sigma_clip : bool
        Whether to do sigma clipping. Sigma clipping is based on the biweight location and biweight midvariance (both unweighted), regardless of the 'method' parameter. Default is None.
    sigma_thresh_low : float
        Number of sigma for low outlier rejection. Default is 4.
    sigma_thresh_high : float
        Number of sigma for high outlier rejection. Default is 4.
    thresh_low : float
        Low threshold for outlier rejection. Default is None.
    thresh_high : float
        High threshold for outlier rejection. Default is None.
    num_mask_low : int
        Number of low outliers to mask. Default is None.
    num_mask_high : int
        Number of high outliers to mask. Default is None.
    min_batch_size : int
        Minimum batch size for sigma clipping. Default is 3.
    maxiters : int
        Maximum number of iterations for sigma clipping. Default is 50.
    error_calc : str
        Method for calculating the error - 'measure' or 'propagate'. Default is 'propagate'.
    data_attr : str
        Name of the data attribute in the input models to be combined. Default is 'data'.
    err_attr : str
        Name of the error attribute in the input models to be combined. Default is 'err' if available.
    var_rnoise_attr : str
        Name of the read noise variance attribute in the input models to be combined. Default is 'var_rnoise' if available.
    var_poisson_attr : str
        Name of the Poisson noise variance attribute in the input models to be combined. Default is 'var_poisson' if available.
    dq_attr : str
        Name of the DQ attribute in the input models to be combined. Default is 'dq' if available.
    
    Returns
    -------
    output
        The coadded science data model with combined data, error, and DQ arrays (same type as input).
    """
    spec = """
        method = string(default = 'wmean') # Method for combining the frames - 'mean', 'wmean', 'median', 'wmedian'. Default is 'wmean'.
        do_sigma_clip = boolean(default = None) # Whether to do sigma clipping. Sigma clipping is based on the biweight location and biweight midvariance (both unweighted), regardless of the 'method' parameter.
        sigma_thresh_low = float(default = 4) # Number of sigma for low outlier rejection.
        sigma_thresh_high = float(default = 4) # Number of sigma for high outlier rejection.
        thresh_low = float(default = None) # Low threshold for outlier rejection.
        thresh_high = float(default = None) # High threshold for outlier rejection.
        num_mask_low = integer(default = None) # Number of low outliers to mask.
        num_mask_high = integer(default = None) # Number of high outliers to mask.
        min_batch_size = integer(default = 3) # Minimum batch size for sigma clipping.
        maxiters = integer(default = 50) # Maximum number of iterations for sigma clipping.
        error_calc = string(default = 'propagate') # Method for calculating the error - 'measure' or 'propagate'. Default is 'propagate'.
        data_attr = string(default = 'data') # Name of the data attribute in the input models to be combined.
        err_attr = string(default = 'err') # Name of the error attribute in the input models to be combined.
        var_rnoise_attr = string(default = 'var_rnoise') # Name of the read noise variance attribute in the input models to be combined.
        var_poisson_attr = string(default = 'var_poisson') # Name of the Poisson noise variance attribute in the input models to be combined.
        dq_attr = string(default = 'dq') # Name of the DQ attribute in the input models to be combined.
    """

    class_alias = "coadd_frames"

    def process(self, input):
        input_models = [self.open_model(f) for f in input]
        input_frames = make_frame_batch(
            input_models,
            attrs=(
                self.data_attr,
                self.err_attr,
                self.var_rnoise_attr,
                self.var_poisson_attr,
                self.dq_attr,
            ),
        )
        result = coadd_frames(
            input_frames,
            method=self.method, error_calc=self.error_calc,
            sigma_thresh_low=self.sigma_thresh_low, sigma_thresh_high=self.sigma_thresh_high,
            thresh_low=self.thresh_low, thresh_high=self.thresh_high,
            num_mask_low=self.num_mask_low, num_mask_high=self.num_mask_high,
            min_batch_size=self.min_batch_size,
            maxiters=self.maxiters,
            do_sigma_clip=self.do_sigma_clip,
            dq_reduce='or'
        )
        output_model_class = input_models[0].__class__
        data_kwargs = {
            f'{self.data_attr}': result['data'],
            f'{self.err_attr}': result['err'],
            f'{self.dq_attr}': result['dq'],
            f'{self.var_rnoise_attr}': result['var_rnoise'],
            f'{self.var_poisson_attr}': result['var_poisson']
        }
        output_model = output_model_class.from_datamodels(
            input_models,
            **data_kwargs
        )
        
        return output_model