from jwst.stpipe import Step
from .. import datamodels
from ..datamodels import DarkModel
from . import dark_sub
import stdatamodels

from ..utils.subarray import get_subarray_model


__all__ = ["DarkCurrentStep"]


class DarkCurrentStep(Step):
    """
    DarkCurrentStep: Performs dark current correction by subtracting
    dark current reference data from the input science data model.
    """

    spec = """
        dark_output = output_file(default = None) # Dark model subtracted
    """

    reference_file_types = ["dark"]

    def process(self, input):

        # Open the input data model
        with self.open_model(input) as input_model:

            # Get the name of the dark reference file to use
            self.dark_name = self.get_reference_file(input_model, "dark")
            self.log.info("Using DARK reference file %s", self.dark_name)

            # Check for a valid reference file
            if self.dark_name == "N/A":
                self.log.warning("No DARK reference file found")
                self.log.warning("Dark current step will be skipped")
                result = input_model.copy()
                result.meta.cal_step.dark = "SKIPPED"
                return result

            # Create name for the intermediate dark, if desired.
            dark_output = self.dark_output
            if dark_output is not None:
                dark_output = self.make_output_path(
                    None, basepath=dark_output, ignore_use_model=True
                )

            # Open the dark ref file data model - based on Instrument
            dark_model = DarkModel(self.dark_name)

            dark_model = get_subarray_model(input_model, dark_model)

            # Do the dark correction
            result = dark_sub.do_correction(input_model, dark_model, dark_output)
            dark_model.close()

        return result
