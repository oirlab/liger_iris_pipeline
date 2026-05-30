from .. import datamodels
from ..stpipe.base_pipeline import LigerIRISPipeline
from ..dq_init import DQInitStep
from ..saturation.saturation_step import SaturationCheckStep
from ..bias_subtraction.bias_step import BiasSubtractionStep
from ..nonlinear_correction.nonlincorr_step import NonlinearCorrectionStep
from ..jump_detection.jump_detection_step import JumpDetectionStep
from ..gain.make_gain_step import MakeGainStep
from ..ramp_fitting.fit_ramp_step import RampFitStep
from ..coadd.coadd_frames_step import CoaddFramesStep
from ..detector_flat.make_detector_flat_step import MakeDetectorFlatStep
from ..dark_subtraction.dark_step import DarkSubtractionStep
from ..gain.gain_step import GainStep
from ..detector_flat.detector_flat_step import DetectorFlatStep
from typing import Sequence

import logging
logger = logging.getLogger(__name__)

__all__ = ['ProcessDetFlatsPipeline']


class ProcessDetFlatsPipeline(LigerIRISPipeline):
    """
    Pipeline to process detector flat frames and create a detector flat calibration and gain calibration.

    Steps
    -----
    - ``dq_init`` - `DQInitStep`
    - ``sat_check`` - `SaturationCheckStep`
    - ``bias_sub`` - `BiasSubtractionStep`
    - ``nonlin_corr`` - `NonlinearCorrectionStep`
    - ``jump_det`` - `JumpDetectionStep`
    - ``make_gain`` - `MakeGainStep`
    - ``ramp_fit`` - `RampFitStep`
    - ``dark_sub`` - `DarkSubtractionStep`
    - ``gain`` - `GainStep`
    - ``coadd_frames`` - `CoaddFramesStep`
    - ``make_detflat`` - `MakeDetectorFlatStep`
    """

    class_alias = "process_detflats"

    step_defs = {
        'dq_init': DQInitStep,
        'sat_check': SaturationCheckStep,
        'bias_sub': BiasSubtractionStep,
        'nonlin_corr': NonlinearCorrectionStep,
        'jump_det': JumpDetectionStep,
        'make_gain': MakeGainStep,
        'ramp_fit': RampFitStep,
        'dark_sub': DarkSubtractionStep,
        'gain': GainStep,
        'coadd_frames': CoaddFramesStep,
        'make_detflat': MakeDetectorFlatStep,
    }

    def process(self, input):

        # Making sure that the input is a list of models for processing
        if isinstance(input, (datamodels.LigerIRISDataModel, str)):
            _input_list = [input]
        if  isinstance(input, Sequence):
            _input_list = input

        # First, loop over all inputs to apply DQ init, saturation check, and bias subtraction
        results = []
        logger.info(f"Looping over a list of {len(_input_list)} inputs to apply dq_init, saturation, bias subtraction, and nonlin_corr.")
        for k, _input in enumerate(_input_list):
            logger.info(f"Processing input {k+1}/{len(_input_list)}: {_input}")
            model_to_process = self.open_model(_input)
            _result = self.dq_init.run(model_to_process)
            _result = self.sat_check.run(_result)
            _result = self.bias_sub.run(_result)
            _result = self.nonlin_corr.run(_result)
            _result = self.jump_det.run(_result)
            results.append(_result)

        # Fit gain using all processed inputs
        gain_result = self.make_gain.run(results)

        # Register the detector gain calibration to the calibration database
        # self.register_gain_cal.run(gain_result)

        logger.info(f"Continue loop over inputs to apply ramp_fit, dark, and det_gain.")
        for k, _result in enumerate(results):
            logger.info(f"Processing input {k+1}/{len(results)}: {_result}")
            _result = self.ramp_fit.run(_result)
            _result = self.dark_sub.run(_result)
            _result = self.gain.run(_result)
            results[k] = _result

        # Get the flat field using all processed inputs. Coadding first.
        coadded_rate = self.coadd_frames.run(results)
        detflat_result = self.make_detflat.run(coadded_rate)

        # Register the detector gain calibration to the calibration database
        # self.register_det_flat_cal.run(detflat_result)

        # logger.info(f"Continue loop over inputs to apply flat fielding.")
        # for k, _result in enumerate(results):
        #     logger.info(f"Processing input {k+1}/{len(results)}: {_result}")
        #     _result = self.detflat.run(_result)
        #     results[k] = _result

        self.results = results

        return dict(gain=gain_result, detflat=detflat_result)