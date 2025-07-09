

from ..base_step import LigerIRISStep
from .nonlinear_correction_numba import correct_nonlinearity

import numpy as np

__all__ = ["NonlinearCorrectionStep"]


class NonlinearCorrectionStep(LigerIRISStep):

    class_alias = "nonlin_corr"

    spec = """
        nonlin = is_string_or_datamodel(default=None) # Reference file for nonlinearity correction
    """

    def process(self, input):
        """
        Step for Nonlinearity correction
        """
        # Load the input data model
        with self.open_model(input) as input_model:

            # Result
            model_result = input_model.copy()

            # Get the name of the nonlin reference file to use
            if self.nonlin is None:
                self.nonlin_filename = self.get_reference_file(input_model, "nonlin")
                nonlin_model = self.open_model(self.nonlin_filename)
            else:
                nonlin_model = self.open_model(self.nonlin)
                self.nonlin_filename = nonlin_model._filepath
            
            self.log.info(f"Using nonlin reference file {self.nonlin_filename}")

            # Alias coeffs and utr times
            coeffs = nonlin_model.coeffs

            # Correct the nonlinearity
            data = model_result.data.astype(np.float32)
            coeffs = coeffs.astype(np.float32)
            model_result.data = correct_nonlinearity(data, coeffs)

            # Close the nonlinearity file
            nonlin_model.close()

            self.status = "COMPLETE"

        return model_result