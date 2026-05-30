from ..stpipe.base_step import LigerIRISStep
from .. import datamodels
from ..utils.subarray import get_subarray_model
from ..calibrations import DQSelector

import logging

logger = logging.getLogger(__name__)


__all__ = ["DQInitStep"]

class DQInitStep(LigerIRISStep):
    """
    Initialize the Data Quality extension from the dqmask reference file.

    Flags from the appropriate static dq reference file in are assigned to all reads in the input dataset - it is assumed that flags in the dq reference file are pixel-dependent only and do not vary with exposure. Read (or signal) dependent flags (e.g. saturation) are assigned in later steps.

    Parameters
    ----------
    input : RampModel
        Input ramp model. More datamodels may be considered in the future to assist with development, but dq_init should always be applied to the ramp model under normal operations.

    Calibrations
    ------------
    dq : DQModel
    
    Returns
    -------
    RampModel
        Output ramp model with dq initialized.
    """

    calibrations = {
        'dq' : {
            'selector': DQSelector,
            'selector_kwargs': {}
        }
    }
    class_alias = "dq_init"

    def process(self, input):

        # Open the input model
        input_model = self.open_model(input)

        # Get output model
        if not isinstance(input_model, datamodels.ProcessedRampModel):
            output_model = datamodels.ProcessedRampModel.from_datamodels(
                input_model,
                include_data=True
            )
        else:
            output_model = input_model

        # Retreive the DQ reference file name
        dq_ref, _ = self.get_calibration(output_model, 'dq')
        logger.info(f'Applying DQ reference: {dq_ref}')
        with self.open_model(dq_ref) as dq_model:
            
            # Get subarray model if needed
            dq_model_subarray = get_subarray_model(output_model, dq_model)

            # Initialize the DQ extension if it does not exist
            if hasattr(output_model, 'dq_raw'):
                logger.info('Applying DQ mask to output_model.dq_raw')
                output_model.dq_raw |= dq_model_subarray.dq[None, :, :]
            if hasattr(output_model, 'dq') and output_model.dq is not None:
                logger.info('Applying DQ mask to output_model.dq')
                output_model.dq |= dq_model_subarray.dq
        
        # Return the updated model
        return output_model