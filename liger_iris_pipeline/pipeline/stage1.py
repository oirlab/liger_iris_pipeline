#!/usr/bin/env python
import logging
from collections import defaultdict
from .base_pipeline import LigerIRISPipeline
from liger_iris_pipeline import datamodels
from ..associations import L0Association

# step imports
from ..readout import NonlinearCorrectionStep, FitRampStep

__all__ = ['Stage1Pipeline']


class Stage1Pipeline(LigerIRISPipeline):
    """
    Stage 1 pipeline to process a series of raw reads to slope maps.
    
    Steps:
        NonlinCorrectionStep
        FitRampStep
    """

    # Define aliases to steps
    step_defs = {
        "nonlinear_correction": NonlinearCorrectionStep,
        "ramp_fit": FitRampStep,
    }

    # start the actual processing
    def process(self, input):
        with datamodels.RampModel(input) as input_model:
            result = self.nonlinear_correction.run(input_model)
            result = self.ramp_fit.run(result)
        return result