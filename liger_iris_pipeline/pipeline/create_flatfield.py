import liger_iris_pipeline.datamodels as datamodels
from .base_pipeline import LigerIRISPipeline
from ..combine_frames import CombineFramesStep
from ..dark_subtraction import DarkSubtractionStep
from ..normalize import NormalizeStep

__all__ = ["CreateFlatfield"]


class CreateFlatfield(LigerIRISPipeline):
    """
    Creates a master flatfield frame from a set of uncalibrated L1 frames.

    Steps:
        - DarkSubtraction
        - CombineFrames
        - Normalize
    """

    # Define alias to steps
    step_defs = {
        "dark_sub" : DarkSubtractionStep,
        "combine_frames" : CombineFramesStep,
        "normalize" : NormalizeStep
    }

    def process(self, input : list[datamodels.IFUImageModel | datamodels.ImagerModel | str]):
        result = []
        for _input in input:
            result.append(self.dark_sub.run(_input))
        result = self.combine_frames.run(result)
        result = self.normalize.run(result)
        flat = datamodels.FlatModel(data=result.data, err=result.err, dq=result.dq)
        flat.meta._instance.update(result.meta._instance)
        flat.meta.ref_type = "flat" # TODO: Check if this is the right way to set the reftype
        return flat