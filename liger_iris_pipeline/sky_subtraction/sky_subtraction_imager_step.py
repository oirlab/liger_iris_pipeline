import numpy as np


from .. import datamodels
from ..base_step import LigerIRISStep
from ..utils.subarray import get_subarray_model

__all__ = ["SkySubtractionImagerStep"]


class SkySubtractionImagerStep(LigerIRISStep):
    """
    SkySubtractionImagerStep:  Sky subtraction for imager from existing sky file.
    """

    def process(self, input, sky_bkg):
        result = input.copy()
        with datamodels.open(input) as input_model, \
            datamodels.open(sky_bkg) as bkg_model:

            # Get subarray model
            bkg_model = get_subarray_model(input_model, bkg_model)

            # Subtract the average background from the member
            self.log.debug(f"Subtracting background from {input_model.meta.filename} with {bkg_model.meta.filename}")
            
            # Subtract the SCI arrays
            result.data = input_model.data - bkg_model.data

            # Error handling
            # ...

            # Combine the DQ flag arrays using bitwise OR
            result.dq = np.bitwise_or(input_model.dq, bkg_model.dq)

            # Close the average background image and update the step status
            result.meta.cal_step.sky_back_sub = "COMPLETE"

        return result
    

#### Add more steps here or new files for IFU and methods of calculating sky ####
