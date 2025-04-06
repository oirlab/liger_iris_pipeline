#! /usr/bin/env python

import liger_iris_pipeline
from ..base_step import LigerIRISStep
from .. import datamodels
from ..utils.subarray import get_subarray_model
from .flat_field import apply_flatfield

__all__ = ["FlatFieldStep"]


class FlatFieldStep(LigerIRISStep):
    """Flat-field a science image using a flatfield reference image.
    """

    spec = """
        flat_output_dir = string(default = None) # Path to save the ref flat from CRDS.
        flat = is_string_or_datamodel(default = None) # Flat filename or datamodel to use. If not set, use CRDS to retrieve.
    """

    reference_file_types = ["flat"]
    class_alias = "flat_field"

    def process(self, input):

        # Open the input data model
        with self.open_model(input, _copy=False) as input_model:

            # Get the name of the flat reference file to use
            if self.flat is None:
                self.flat_filename = self.get_reference_file(input_model, "flat")
                flat_model = self.open_model(self.flat_filename)
            else:
                flat_model = self.open_model(self.flat)
                self.flat_filename = flat_model._filename
            self.log.info("Using flat reference file %s", self.flat_filename)

            flat_model = get_subarray_model(input_model, flat_model)

            # Do the flat-field correction
            result = apply_flatfield(input_model, flat_model)

            # Save the flat ref model
            if self.flat_output_dir is not None:
                flat_output_path = self.make_output_path(flat_model, output_dir=self.flat_output_dir)
                flat_model.save(flat_output_path)
            flat_model.close()
            self.status = "COMPLETE"

        return result