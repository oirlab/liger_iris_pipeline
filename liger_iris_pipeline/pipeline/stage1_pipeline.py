from .. import datamodels
from ..stpipe.base_pipeline import LigerIRISPipeline

# step imports
from ..nonlinear_correction import NonlinearCorrectionStep
from ..ramp_fitting import RampFitStep
from ..dq_init import DQInitStep
from ..bias_subtraction import BiasSubtractionStep
from ..saturation import SaturationCheckStep
from ..jump_detection import JumpDetectionStep

__all__ = ['Stage1Pipeline']


class Stage1Pipeline(LigerIRISPipeline):
    """
    The Stage 1 Pipeline processes raw reads to generate rate maps (raw 2D frames).

    Steps
    -----
    - ``dq_init`` - `DQInitStep`
    - ``sat_check`` - `SaturationCheckStep`
    - ``bias_sub`` - `BiasSubtractionStep`
    - ``nonlin_corr`` - `NonlinearCorrectionStep`
    - ``jump_det`` - `JumpDetectionStep`
    - ``ramp_fit`` - `RampFitStep`
    """

    # Define aliases to steps
    step_defs = {
        "dq_init": DQInitStep,
        "sat_check": SaturationCheckStep,
        "bias_sub": BiasSubtractionStep,
        "nonlin_corr": NonlinearCorrectionStep,
        "jump_det" : JumpDetectionStep,
        "ramp_fit": RampFitStep,
    }

    class_alias = "stage1"

    def process(self, input):
        results = []
        if not isinstance(input, list):
            input = [input]
        for _input in input:
            with self.open_model(_input) as model_to_process:
                result = self.dq_init.run(model_to_process)
                result = self.sat_check.run(result)
                result = self.bias_sub.run(result)
                result = self.nonlin_corr.run(result)
                result = self.jump_det.run(result)
                result = self.ramp_fit.run(result)
                results.append(result)
        return results