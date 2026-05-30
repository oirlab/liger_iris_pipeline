from .. import datamodels
from ..stpipe.base_pipeline import LigerIRISPipeline
from ..dq_init import DQInitStep
from ..saturation.saturation_step import SaturationCheckStep
from ..bias_subtraction.bias_step import BiasSubtractionStep
from ..nonlinear_correction.nonlincorr_step import NonlinearCorrectionStep
from ..jump_detection.jump_detection_step import JumpDetectionStep
from ..nonlinear_correction.make_nonlin_step import MakeNonLinStep
from ..ramp_fitting.fit_ramp_step import RampFitStep
from ..saturation.make_saturation_step import MakeSaturationStep
from ..dark_subtraction.dark_step import DarkSubtractionStep
from ..gain.gain_step import GainStep
from ..detector_flat.detector_flat_step import DetectorFlatStep

from typing import Sequence

import logging
logger = logging.getLogger(__name__)

__all__ = ['ProcessSatDetFlatsPipeline']


class ProcessSatDetFlatsPipeline(LigerIRISPipeline):
    """
    Pipeline to process saturated flat frames to create a saturation calibration and nonlinearity calibration.

    Steps
    -----
    - ``dq_init`` - `DQInitStep`
    - ``make_sat`` - `MakeSaturationStep`
    - ``sat_check`` - `SaturationCheckStep`
    - ``bias_sub`` - `BiasSubtractionStep`
    - ``make_nonlin`` - `MakeNonLinStep`
    """

    class_alias = "process_satdetflats"

    step_defs = {
        'dq_init': DQInitStep,
        'make_sat': MakeSaturationStep,
        'sat_check': SaturationCheckStep,
        'bias_sub': BiasSubtractionStep,
        'make_nonlin': MakeNonLinStep,
    }

    def process(self, input):

        # Making sure that the input is a list of models for processing
        if isinstance(input, (datamodels.LigerIRISDataModel, str)):
            _input_list = [input]
        if  isinstance(input, Sequence):
            _input_list = input

        # First, loop over all inputs to apply DQ init, saturation check, and bias subtraction
        results = []
        logger.info(f"Looping over a list of {len(_input_list)} inputs to apply dq_init.")
        for k, _input in enumerate(_input_list):
            logger.info(f"Processing input {k+1}/{len(_input_list)}: {_input}")
            model_to_process = datamodels.open(_input)
            _result = self.dq_init.run(model_to_process)
            results.append(_result)

        # Fit for nonlinearity using all processed inputs
        saturation_result = self.make_sat.run(results)

        # Register the nonlinear correction calibration to the calibration database
        # self.register_nonlin_cal.run(nonlin_result)

        logger.info(f"Running saturation check and bias subtraction on processed inputs.")
        for k, _result in enumerate(results):
            logger.info(f"Processing input {k+1}/{len(results)}: {_result}")
            _result = self.sat_check.run(_result)
            _result = self.bias_sub.run(_result)
            results[k] = _result

        # Fit for nonlinearity using all processed inputs
        nonlin_result = self.make_nonlin.run(results)

        # Register the nonlinear correction calibration to the calibration database
        # self.register_nonlin_cal.run(nonlin_result)

        # logger.info(f"Continue loop over inputs to apply bias, nonlin_corr, jump_detec, ramp_fit, dark_sub, gain_corr, and detflat_corr.")
        # for k, _result in enumerate(results):
        #     logger.info(f"Processing input {k+1}/{len(results)}: {_result}")
        #     _result = self.nonlin_corr.run(_result)
        #     _result = self.jump_det.run(_result)
        #     _result = self.ramp_fit.run(_result)
        #     _result = self.dark_sub.run(_result)
        #     _result = self.gain.run(_result)
        #     _result = self.detflat.run(_result)
        #     results[k] = _result
        self.results = results
        
        return dict(nonlin=nonlin_result, saturation=saturation_result)