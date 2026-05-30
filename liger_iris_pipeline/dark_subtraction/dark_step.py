from ..stpipe.base_step import LigerIRISStep
from .dark_sub import dark_subtraction_rate
from .. import datamodels
from ..utils.subarray import get_subarray_model
from ..calibrations import DarkSelector

import logging

logger = logging.getLogger(__name__)


class DarkSubtractionStep(LigerIRISStep):
    """
    Performs dark current correction by subtracting dark current reference data from the input science data model.

    The appropriate master dark calibration is subtracted from the input data. The input's ``err`` attribute is updated by adding the dark's ``err`` attribute in quadarature. DQ flags are updated with bitwise or.

    Parameters
    ----------
    input : ImagerModel or IFSImageModel
        The input level 1 data model to be dark subtracted.
    max_cores : int, optional
        Maximum number of CPU cores to use.
        Default is 1.

    Calibrations
    ------------
    dark : `DarkModel` - Selector: `DarkSelector`
    
    Returns
    -------
    output
        The dark-subtracted data model (same type as input).
    """

    calibrations = {
        'dark' : {
            'selector': DarkSelector,
            'selector_kwargs': {}
        }
    }

    class_alias = "dark_sub"

    def process(self, input):

        # Open the input model
        input_model = self.open_model(input)
        
        # Retreive the DQ reference file name
        dark, _ = self.get_calibration(input_model, 'dark')
        logger.info(f'Applying Dark reference: {dark}')
        with self.open_model(dark) as dark_model:

            # Get subarray model
            dark_model_subarray = get_subarray_model(input_model, dark_model)

            # Do the dark correction
            dark_subtraction_rate(
                input_model.data, input_model.err, input_model.dq,
                dark_model_subarray.data, dark_model_subarray.err, dark_model_subarray.dq,  
                max_cores=self.max_cores
            )

        # Return the corrected data model
        return input_model