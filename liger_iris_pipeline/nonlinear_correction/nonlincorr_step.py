from ..stpipe.base_step import LigerIRISStep
from .nonlinear_correction_numba import correct_nonlinearity
from ..utils.subarray import get_subarray_model
from ..calibrations import NonlinearCorrectionSelector
from .. import datamodels

import logging

logger = logging.getLogger(__name__)

__all__ = ["NonlinearCorrectionStep"]


class NonlinearCorrectionStep(LigerIRISStep):
    """
    The step divides a sequence of UTR reads by the nonlinear detector response.
    
    The data is transformed with a polynomial which describes the nonlinear response of the detector.

    Parameters
    ----------
    input : RampModel
        Input ramp model to correct.
    max_cores : int, optional
        Maximum number of CPU cores to use.
        Default is 1.

    Calibrations
    ------------
    nonlin : `NonlinearCorrectionModel` - Selector: `NonlinearCorrectionSelector`

    Returns
    -------
    output : ProcessedRampModel
        The corrected ramp model.
    """

    class_alias = "nonlin_corr"

    calibrations = {
        'nonlin' : {
            'selector' : NonlinearCorrectionSelector,
            'selector_kwargs' : {}
        }
    }

    spec = """
        max_cores = integer(default=1) # Maximum number of CPU cores to use
    """

    def process(self, input):

        # Open the input data model
        input_model = self.open_model(input)

        # Get output model
        if not isinstance(input_model, datamodels.ProcessedRampModel):
            output_model = datamodels.ProcessedRampModel.from_datamodels(
                input_model,
                include_data=True
            )
        else:
            output_model = input_model

        # Get the name of the nonlin reference file to use
        nonlin_ref, _ = self.get_calibration(output_model, "nonlin")
        logger.info(f"Using nonlin reference file: {nonlin_ref}")

        # Open the nonlinear model
        with self.open_model(nonlin_ref) as nonlin_model:

            # Get subarray model if needed
            nonlin_model_subarray = get_subarray_model(output_model, nonlin_model)

            # Correct the nonlinearity
            correct_nonlinearity(
                ramps=output_model.data,
                dq_raw=output_model.dq_raw,
                dq=output_model.dq,
                coeffs=nonlin_model_subarray.coeffs,
                nonlin_max=nonlin_model_subarray.nonlin_max,
                nonlin_dq=nonlin_model_subarray.dq,
                max_cores=self.max_cores
            )

        # Return
        return output_model