from .. import datamodels
from ..stpipe.base_pipeline import LigerIRISPipeline

from ..dq_init import DQInitStep
from ..bias_subtraction.make_bias_step import MakeBiasStep
from ..saturation.saturation_step import SaturationCheckStep
from ..bias_subtraction.bias_step import BiasSubtractionStep
from ..nonlinear_correction.nonlincorr_step import NonlinearCorrectionStep
from ..jump_detection.jump_detection_step import JumpDetectionStep
from ..read_noise.make_read_noise_step import MakeReadNoiseStep
from ..ramp_fitting.fit_ramp_step import RampFitStep
from ..coadd.coadd_frames_step import CoaddFramesStep
from ..dark_subtraction.make_dark_step import MakeDarkStep
from ..dark_subtraction.dark_step import DarkSubtractionStep
from ..gain.gain_step import GainStep
from ..detector_flat.detector_flat_step import DetectorFlatStep
from typing import Sequence

import logging
logger = logging.getLogger(__name__)

__all__ = ['ProcessDarksPipeline']


class ProcessDarksPipeline(LigerIRISPipeline):
    """
    Calibration pipeline to generate dark and readnoise calibration files from raw dark UTR data.

    Steps
    -----
    - ``dq_init`` - `DQInitStep`
    - ``make_bias`` - `MakeBiasStep`
    - ``sat_check`` - `SaturationCheckStep`
    - ``bias_sub`` - `BiasSubtractionStep`
    - ``nonlin_corr`` - `NonlinearCorrectionStep`
    - ``jump_det`` - `JumpDetectionStep`
    - ``make_rn`` - `MakeReadNoiseStep`
    - ``ramp_fit`` - `RampFitStep`
    - ``coadd_frames`` - `CoaddFramesStep`
    - ``make_dark`` - `MakeDarkStep`

    Returns
    -------
    dict
        A dictionary containing the derived read noise and dark calibration models with keys "read_noise" and "dark", respectively:

            'read_noise' : ReadNoiseModel
                The derived read noise calibration model.
            'dark' : DarkModel
                The derived dark calibration model.

    """
    step_defs = {
        'dq_init': DQInitStep,
        'make_bias': MakeBiasStep,
        'sat_check': SaturationCheckStep,
        'bias_sub': BiasSubtractionStep,
        'nonlin_corr': NonlinearCorrectionStep,
        'jump_det': JumpDetectionStep,
        'make_rn': MakeReadNoiseStep,
        'ramp_fit': RampFitStep,
        'coadd_frames': CoaddFramesStep,
        'make_dark': MakeDarkStep,
    }

    class_alias = "process_darks"

    def process(self, input):

        # Making sure that the input is a list of models for processing
        if isinstance(input, (datamodels.LigerIRISDataModel, str)):
            _input_list = [input]
        if  isinstance(input, Sequence):
            _input_list = input

        # First, loop over all inputs to apply DQ init
        results = []
        logger.info(f"Looping over a list of {len(_input_list)} inputs to apply dq_init, saturation, bias subtraction, nonlin_corr, and jump detection.")
        for k, _input in enumerate(_input_list):
            logger.info(f"Initializaing DQ map for input {k+1}/{len(_input_list)}: {_input}")
            model_to_process = datamodels.open(_input)
            _result = self.dq_init.run(model_to_process)
            results.append(_result)

        # Make the bias calibration
        if not self.make_bias.skip:
            bias_result = self.make_bias.run(results)
        else:
            bias_result = None

        # Run remaining steps on each input
        for k, result in enumerate(results):
            _result = self.sat_check.run(result)
            _result = self.bias_sub.run(_result)
            _result = self.nonlin_corr.run(_result)
            _result = self.jump_det.run(_result)
            results[k] = _result

        # Fit read noise using all processed inputs
        rn_result = self.make_rn.run(results)

        logger.info(f"Continue loop over inputs to apply ramp_fit.")
        for k, _result in enumerate(results):
            logger.info(f"Processing input {k+1}/{len(results)}: {_result}")
            _result = self.ramp_fit.run(_result)
            results[k] = _result

        # Coadd rate maps
        coadded_rate = self.coadd_frames.run(results)

        # Create dark from coadded rate map
        # (flag hot pixels, convert to dark model, etc.)
        dark_result = self.make_dark.run(coadded_rate)

        # Store ancilarry results, TBD on better mechanism with stpipe
        self.results = results

        return dict(bias_result=bias_result, read_noise=rn_result, dark=dark_result)