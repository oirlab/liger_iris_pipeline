

from ..base_step import LigerIRISStep
from ..datamodels import RampModel, NonlinearReadoutParametersModel
from .nonlinear_correction_numba import correct_nonlinearity

import numpy as np

__all__ = ["NonlinCorrectionStep"]


class NonlinCorrectionStep(LigerIRISStep):

    reference_file_types = ["nonlincoeff"]

    class_alias = "nonlincorr"

    def process(self, input):
        """
        Step for Nonlinearity correction
        """
        # Load the input data model
        with RampModel(input) as input_model:

            # Result
            model_result = input_model.copy()

            # Get the reference file of coefficients
            nonlin_coeff_file = self.get_reference_file(input_model, "nonlincoeff")
            nonlin_model = NonlinearReadoutParametersModel(nonlin_coeff_file)
            coeffs = nonlin_model.coeffs

            # Vector of read times for all pixels
            input_times = model_result.times

            # Correct the nonlinearity
            model_result.data = correct_nonlinearity(input_times.astype(np.float32), model_result.data.astype(np.float32), coeffs.astype(np.float32))

            # Close the nonlinearity file
            nonlin_model.close()

            self.status = "COMPLETE"

        return model_result
