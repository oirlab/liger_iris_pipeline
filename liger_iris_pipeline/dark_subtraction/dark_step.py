#from .. import datamodels
from ..base_step import LigerIRISStep
from . import dark_sub
from .. import datamodels

from ..utils.subarray import get_subarray_model


__all__ = ["DarkSubtractionStep"]


class DarkSubtractionStep(LigerIRISStep):
    """
    DarkSubtractionStep: Performs dark current correction by subtracting
    dark current reference data from the input science data model.
    """

    spec = """
        dark_output_dir = string(default = None) # Path to save the ref dark from CRDS.
    """

    reference_file_types = ["dark"]
    class_alias = "dark_sub"

    def process(self, input):

        # Open the input data model
        with datamodels.open(input) as input_model:

            # Get the name of the dark reference file to use
            self.dark_filename = self.get_reference_file(input_model, "dark")
            self.log.info("Using DARK reference file %s", self.dark_filename)

            # Check for a valid reference file
            if self.dark_filename == "N/A" or self.dark_filename is None:
                self.log.warning("No DARK reference file found, skipping dark subtraction")
                self.status = "SKIPPED"
                return result

            # Open the dark ref file data model
            dark_model = datamodels.DarkModel(self.dark_filename)
            dark_model = get_subarray_model(input_model, dark_model)

            # Do the dark correction
            result = dark_sub.subtract_dark(input_model, dark_model)

            # Save the dark ref model
            if self.dark_output_dir is not None:
                # TODO: HERE !!!! Make function make_output_path. Should be easy with correct datamodels
                dark_path = self.make_output_path(dark_model, output_dir=self.dark_output_dir)
                dark_model.save(dark_path)
            dark_model.close()
            self.status = "COMPLETE"

        return result