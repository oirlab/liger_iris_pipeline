from ..base_step import LigerIRISStep
from .. import datamodels
from . import normalize


__all__ = ["NormalizeStep"]


class NormalizeStep(LigerIRISStep):
    """
    NormalizeStep: Normalize a frame by dividing
    by its own mean, median or mode
    """

    class_alias = "normalize"

    spec = """
        method = string(default='median')
    """

    def process(self, input):
        with self.open_model(input, _copy=True) as input_model:
            result = normalize.do_correction(input_model, method=self.method)

        self.status = "COMPLETE"

        return result
