#! /usr/bin/env python
from ..base_step import LigerIRISStep
from .. import datamodels
from ..datamodels import ImagerModel, LigerIRISDataModel

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

    class_alias = "assign_wcs"

    def process(self, input):
        reference_file_names = {}
        with self.open_model(input, _copy=False) as input_model:
            # Get reference files
            for reftype in self.reference_file_types:
                reffile = self.get_reference_file(input_model, reftype)
                reference_file_names[reftype] = reffile if reffile else ""
            log.debug(f"reference files used in assign_wcs: {reference_file_names}")

            # Assign wcs
            result = load_wcs(input_model, reference_file_names)
            self.status = "COMPLETE"

        return result
