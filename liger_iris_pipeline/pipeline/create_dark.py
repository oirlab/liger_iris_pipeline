import liger_iris_pipeline.datamodels as datamodels
from .base_pipeline import LigerIRISPipeline
from ..combine_frames import CombineFramesStep

__all__ = ["CreateDark"]


class CreateDark(LigerIRISPipeline):
    """
    Creates a master dark frame from a set of uncalibrated L1 frames.

    Steps:
        - CombineFrames
    """

    # Define alias to steps
    step_defs = {
        "combine_frames" : CombineFramesStep
    }

    def process(self, input : list[datamodels.IFUImageModel | datamodels.ImagerModel | str]):
        result = self.combine_frames.run(input)
        dark = datamodels.DarkModel(data=result.data, err=result.err, dq=result.dq)
        dark.meta._instance.update(result.meta._instance)
        dark.meta.reftype = "dark" # TODO: Check if this is the right way to set the reftype
        return dark