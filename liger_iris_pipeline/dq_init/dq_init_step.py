#! /usr/bin/env python

from ..base_step import LigerIRISStep
from .. import datamodels
from . import dq_initialization

__all__ = ["DQInitStep"]

class DQInitStep(LigerIRISStep):
    """Initialize the Data Quality extension from the
    mask reference file.

    The dq_init step initializes the pixeldq attribute of the
    input datamodel using the MASK reference file.  For some
    FGS exp_types, initalize the dq attribute of the input model
    instead.  The dq attribute of the MASK model is bitwise OR'd
    with the pixeldq (or dq) attribute of the input model.
    """

    reference_file_types = ['dq']
    class_alias = "dq_init"

    def process(self, input):
        """Perform the dq_init calibration step

        Parameters
        ----------
        input : JWST datamodel
            input jwst datamodel

        Returns
        -------
        LigerIRISDataModel : The output datamodel.
        """

        # TODO: Implement me

        # Retreive the mask reference file name
        self.mask_filename = self.get_reference_file(input_model, 'mask')
        self.log.info('Using MASK reference file %s', self.mask_filename)
        self.status = "COMPLETE"

        # Check for a valid reference file
        if self.mask_filename == 'N/A':
            self.log.warning('No MASK reference file found')
            self.log.warning('DQ initialization step will be skipped')
            result = input_model.copy()
            self.status = "SKIPPED"
            return result

        # Apply the step
        result = dq_initialization.correct_model(input_model, mask_model)
        self.status = "COMPLETE"

        # Close the data models for the input and ref file
        input_model.close()
        mask_model.close()

        return result
