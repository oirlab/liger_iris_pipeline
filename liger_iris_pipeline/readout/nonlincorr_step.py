

from ..base_step import LigerIRISStep
from .nonlinear_correction_numba import correct_nonlinearity

import numpy as np

__all__ = ["NonlinearCorrectionStep"]


class NonlinearCorrectionStep(LigerIRISStep):

    reference_file_types = ["nonlincoeff"]

    class_alias = "nonlincorr"

    spec = """
        nonlincoeff_ouput_dir = string(default=None) # Output directory for the nonlinearity coefficients
        nonlincoeff = is_string_or_datamodel(default=None) # Reference file of coefficients
    """

    def process(self, input):
        """
        Step for Nonlinearity correction
        """
        # Load the input data model
        with self.open_model(input, _copy=False) as input_model:

            # Result
            model_result = input_model.copy()

            # Get the name of the nonlincoeff reference file to use
            if self.nonlincoeff is None:
                self.nonlincoeff_filename = self.get_reference_file(input_model, "nonlincoeff")
                nonlincoeff_model = self.open_model(self.nonlincoeff_filename)
            else:
                nonlincoeff_model = self.open_model(self.nonlincoeff)
                self.nonlincoeff_filename = nonlincoeff_model._filename
            
            self.log.info(f"Using nonlincoeff reference file {self.nonlincoeff_filename}")

            # Alias coeffs and utr times
            coeffs = nonlincoeff_model.coeffs
            input_times = model_result.times

            # Correct the nonlinearity
            data = model_result.data.astype(np.float32)
            coeffs = coeffs.astype(np.float32)
            model_result.data = correct_nonlinearity(
                data,
                coeffs,
            )

            # Close the nonlinearity file
            nonlincoeff_model.close()

            self.status = "COMPLETE"

        return model_result