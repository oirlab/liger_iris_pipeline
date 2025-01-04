#! /usr/bin/env python
from ..base_step import LigerIRISStep
from .. import datamodels
from ..datamodels import ImagerModel

import logging

from .assign_wcs import load_wcs

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

__all__ = ["AssignWCSStep"]


class AssignWCSStep(LigerIRISStep):
    """
    """

    # eventually ['distortion' , 'specwcs', 'wavelengthrange']
    reference_file_types = []

    def process(self, input, *args, **kwargs):
        reference_file_names = {}
        if isinstance(input, str):
            input_model = datamodels.open(input)
        else:
            input_model = input

        # If input type is not supported, log warning, set to 'skipped', exit
        if not (isinstance(input_model, ImagerModel)):
            log.warning("Input dataset type is not supported.")
            log.warning("assign_wcs expects ImageModel as input.")
            log.warning("Skipping assign_wcs step.")
            result = input_model.copy()
            result.meta.cal_step.assign_wcs = "SKIPPED"
        else:
            # Get reference files
            for reftype in self.reference_file_types:
                reffile = self.get_reference_file(input_model, reftype)
                reference_file_names[reftype] = reffile if reffile else ""
            log.debug(f"reference files used in assign_wcs: {reference_file_names}")

            # Assign wcs
            result = load_wcs(input_model, reference_file_names)

        # Close model if opened manually
        if isinstance(input, str):
            input_model.close()

        return result
