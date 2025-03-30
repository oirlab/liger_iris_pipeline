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
        dark = is_string_or_datamodel(default = None) # Dark filename or datamodel to use. If not set, use CRDS to retrieve.
    """

    reference_file_types = ["dark"]
    class_alias = "dark_sub"

    def process(self, input):

        # Open the input data model
        with self.open_model(input) as input_model:

            # Get the name of the dark reference file to use
            if self.dark is None:
                self.dark_filename = self.get_reference_file(input_model, "dark")
                dark_model = self.open_model(self.dark_filename)
            else:
                dark_model = self.open_model(self.dark)
                self.dark_filename = dark_model._filename
            self.log.info("Using dark reference file %s", self.dark_filename)

            # Get subarray model if needed
            dark_model = get_subarray_model(input_model, dark_model)

            # Do the dark correction
            result = dark_sub.subtract_dark(input_model, dark_model)

            # Save the dark ref model
            if self.dark_output_dir is not None:
                dark_output_path = self.make_output_path(dark_model, output_dir=self.dark_output_dir)
                dark_model.save(dark_output_path)
            dark_model.close()
            self.status = "COMPLETE"

        return result