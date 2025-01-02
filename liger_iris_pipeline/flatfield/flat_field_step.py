#! /usr/bin/env python

import liger_iris_pipeline
from ..base_step import LigerIRISStep
from .. import datamodels
from . import flat_field

__all__ = ["FlatFieldStep"]


class FlatFieldStep(LigerIRISStep):
    """Flat-field a science image using a flatfield reference image.
    """

    reference_file_types = ["flat"]

    def process(self, input):
        input_model = datamodels.open(input)

        # Figure out what kind of input data model is in use.
        self.log.debug("Input is {}".format(input_model.__class__.__name__))

        self.flat_filename = self.get_reference_file(input_model, "flat")
        self.log.debug("Using FLAT reference file: %s", self.flat_filename)

        # Check for a valid reference file
        missing = False
        if self.flat_filename == "N/A":
            self.log.warning("No FLAT reference file found")
            missing = True
        if missing:
            self.log.warning("Flat-field step will be skipped")
            return self.skip_step(input_model)

        self.log.debug("Opening flat as FlatModel")
        flat_model = liger_iris_pipeline.FlatModel(self.flat_filename)

        # Do the flat-field correction
        output_model = flat_field.do_correction(
            input_model,
            flat_model,
        )

        # Close the inputs
        input_model.close()
        flat_model.close()

        return output_model

    def skip_step(self, input_model):
        """Set the calibration switch to SKIPPED.

        This method makes a copy of input_model, sets the calibration
        switch for the flat_field step to SKIPPED in the copy, closes
        input_model, and returns the copy.
        """

        result = input_model.copy()
        result.meta.cal_step.flat_field = "SKIPPED"
        input_model.close()
        return result
