from .. import datamodels
from ..stpipe.base_step import LigerIRISStep

import numpy as np

import logging

logger = logging.getLogger(__name__)

__all__ = ['BackgroundSubtractionImagerStep']


class BackgroundSubtractionImagerStep(LigerIRISStep):
    """
    Subtracts background from input images.

    Parameters
    ----------
    input : ImagerModel
        The input imager data model to subtract the background from.
    background : ImagerModel, str, optional
        The background model to subtract from the input data.
    do_scale_calc : bool, optional
        Whether to perform scaling calculations when computing background. Default is True.
    scale : float, optional
        Known factor to apply to the background before subtraction. If None, scaling is controlled by do_scale_calc.
    
    Returns
    -------
    ImagerModel
        The background-subtracted science data model.
    """

    spec = """
        background = is_string_or_datamodel(default=None) # Background model to subtract.
        do_scale_calc = boolean(default=True) # Whether to perform scaling calculations when computing background. Default is True.
        scale = float(default=None) # Known factor to apply to the background before subtraction. If None, scaling is controled by do_scale_calc.
    """

    class_alias = "background_sub"

    def process(self, input):
        input_model = self.open_model(input)
        with self.open_model(self.background) as bkg_model:
            if self.scale is not None:
                scale = self.scale
            elif self.do_scale_calc:
                logger.info(f"Calculating scale factor for background subtraction between {input_model} and {bkg_model}")
                # scale = calc_scale_factor(input_model, bkg_model)
                raise NotImplementedError("Scale calculation not yet implemented.")
            else:
                scale = None
            logger.info(f"Subtracting {bkg_model} from {input_model} with scale={scale}")
            subtract_background_imager(input_model, bkg_model, scale=scale)

        return input_model

def subtract_background_imager(
    input_model : datamodels.ImagerModel,
    bkg_model : datamodels.ImagerModel,
    scale : float | None = None,
) -> datamodels.ImagerModel:
    """
    Subtracts the background image model from the input image model.
    Errors are combined in quadrature.
    Data quality flags are combined using a bitwise OR operation.
    Operations are done in-place.
    
    Parameters
    ----------
    input_model : ImagerModel
        The input image model.
    bkg_model : ImagerModel
        The reference image model.
    scale : float | None, optional
        Scaling factor to apply to the background before subtraction. Default is None.
        
    Returns
    -------
    input_model : datamodels.ImagerModel
        The in-place background-corrected imager model.
    """
    if scale is None:
        scale = np.float32(1)
    input_model.data -= bkg_model.data * scale
    input_model.err = np.sqrt(input_model.err**2 + (bkg_model.err * scale)**2)
    input_model.dq |= bkg_model.dq
    return input_model