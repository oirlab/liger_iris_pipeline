import numpy as np


from .. import datamodels
from ..base_step import LigerIRISStep
from ..utils.subarray import get_subarray_model

__all__ = ["SkySubtractionImagerStep"]


class SkySubtractionImagerStep(LigerIRISStep):
    """
    SkySubtractionImagerStep:  Sky subtraction for imager from existing sky file.
    """

    class_alias = "sky_sub"

    def process(self, input, sky_input):
        result = input.copy()
        with datamodels.open(input) as input_model, \
            datamodels.open(sky_input) as sky_model:

            # Get subarray model
            sky_model = get_subarray_model(input_model, sky_model)

            # Subtract the average background from the member
            self.log.debug(f"Subtracting background from {input_model.meta.filename} with {sky_model.meta.filename}")
            
            # Subtract the SCI arrays
            result.data = input_model.data - sky_model.data

            # Error handling
            # ...

            # Combine the DQ flag arrays using bitwise OR
            result.dq = np.bitwise_or(input_model.dq, sky_model.dq)

            self.status = "COMPLETE"

        return result
    

#### Add more steps here or new files for IFU and methods of calculating sky ####
