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

    spec = """
        sky = is_string_or_datamodel(default = None) # Sky filename or datamodel to use.
    """

    def process(self, input):
        with self.open_model(input, copy=True) as input_model, \
            self.open_model(self.sky, copy=False) as sky_model:

            # Result (NOTE: Choose optimal way to handle copying here and with self.open_model)
            result = input_model.copy()

            # Get subarray model
            sky_model = get_subarray_model(input_model, sky_model)

            # Subtract the average background from the member
            self.log.debug(f"Subtracting background from {input_model.meta.filename} with {sky_model.meta.filename}")
            
            # Subtract the SCI arrays
            result.data = input_model.data - sky_model.data

            # Error prop
            result.err = np.sqrt(input_model.err**2 + sky_model.err**2)

            # Combine the DQ flag arrays using bitwise OR
            result.dq = np.bitwise_or(input_model.dq, sky_model.dq)

            self.status = "COMPLETE"

        return result