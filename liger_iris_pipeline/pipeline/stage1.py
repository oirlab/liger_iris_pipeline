from .base_pipeline import LigerIRISPipeline

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
        "nonlin_corr": NonlinearCorrectionStep,
        "ramp_fit": FitRampStep,
    }

    # start the actual processing
    def process(self, input):
        results = []
        for sci in input:
            result = self.nonlin_corr.run(sci)
            result = self.ramp_fit.run(result)
            results.append(result)
        return results