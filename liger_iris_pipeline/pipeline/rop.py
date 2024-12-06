#!/usr/bin/env python
import logging
from collections import defaultdict
import os.path as op

from jwst.associations.load_as_asn import LoadAsLevel2Asn
from .base_pipeline import LigerIRISPipeline
from liger_iris_pipeline import datamodels

# step imports
from ..readout import readoutsamp_step
from ..readout import nonlincorr_step
__all__ = ['rop']

# Define logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)


class ROPPipeline(LigerIRISPipeline):
    """
    Detector1Pipeline for IRIS
    """

    spec = """
        save_calibrated_ramp = boolean(default=False)
    """

    # Define aliases to steps
    step_defs = {
        "nonlincorr": nonlincorr_step.NonlincorrStep,
        "readoutsamp": readoutsamp_step.ReadoutsampStep,
    }

    # start the actual processing
    def process(self, input):
        log.info('Starting ROP Pipeline ...')
        # open the input as a RampModel
        input = datamodels.RampModel(input)
        input = self.nonlincorr(input)
        input = self.readoutsamp(input)
        return input

    def setup_output(self, input):
        # Determine the proper file name suffix to use later
        if input.meta.cal_step.ramp_fit == 'COMPLETE':
            self.suffix = 'rate'
        else:
            self.suffix = 'ramp'
