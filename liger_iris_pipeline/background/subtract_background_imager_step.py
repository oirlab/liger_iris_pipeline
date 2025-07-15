from ..base_step import LigerIRISStep
from .. import datamodels
import numpy as np

__all__ = ['SubtractBackgroundImagerStep', 'subtract_background_imager']


class SubtractBackgroundImagerStep(LigerIRISStep):
    """
    Subtracts the background image model from the input image model.
    Errors are combined in quadrature.
    Data quality flags are combined using a bitwise OR operation.
    """

    spec = """
        background = is_string_or_datamodel(default=None) # Reference image model to subtract from the input model.
        scale = float(default=1.0) # Scale factor to apply to the background before subtraction.
    """

    class_alias = "subtract_bkg"

    def process(self, input : str | datamodels.ImagerModel):
        with self.open_model(input) as input_model, \
             self.open_model(self.background) as bkg_model:
            output_model = input_model.copy()
            output_model = subtract_background_imager(output_model, bkg_model, scale=self.scale)
        self.status = "COMPLETE"
        return output_model


def subtract_background_imager(
    input_model : datamodels.ImagerModel,
    bkg_model : datamodels.ImagerModel,
    scale : float = 1.0
) -> dict:
    """
    Subtracts the background image model from the input image model.
    Errors are combined in quadrature.
    Data quality flags are combined using a bitwise OR operation.
    
    Args:
        input_model (ImagerModel) : The input image model.
        bkg_model (ImagerModel) : The reference image model.
        
    Returns:
        ImagerModel: A dictionary containing the sky level, error, and number of pixels used.
    """
    input_model.data -= bkg_model.data * scale
    input_model.err = np.sqrt(input_model.err**2 + (bkg_model.err * scale)**2)
    input_model.dq |= bkg_model.dq
    return input_model