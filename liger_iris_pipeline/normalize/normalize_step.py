from ..base_step import LigerIRISStep
from .. import datamodels
from . import normalize


__all__ = ["NormalizeStep"]


class NormalizeStep(LigerIRISStep):
    """
    NormalizeStep: Normalize a frame by dividing
    by its own mean, median or mode
    """

    spec = """
        method = string(default='median')
    """

    def process(self, input):
        if isinstance(input, str):
            with datamodels.open(input) as input_model:
                result = normalize.do_correction(input_model, method=self.method)
        else:
            result = normalize.do_correction(input, method=self.method)

        return result
