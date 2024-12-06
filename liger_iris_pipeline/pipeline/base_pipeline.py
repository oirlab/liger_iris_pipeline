from stpipe import Pipeline
from ..base_step import LigerIRISStep

__all__ = [
    "LigerIRISPipeline"
]

class LigerIRISPipeline(Pipeline, LigerIRISStep):
    pass