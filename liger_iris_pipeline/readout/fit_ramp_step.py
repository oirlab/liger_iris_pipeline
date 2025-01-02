

from ..base_step import LigerIRISStep
from ..datamodels import RampModel, ImagerModel, IFUImageModel
from .fit_ramp_numba import fit_ramps_utr, fit_ramps_mcds

import numpy as np

__all__ = ["FitRampStep"]


class FitRampStep(LigerIRISStep):

    spec = """
        method = string(default='utr')  # Ramp fit method. Options are 'utr' and 'mcds'.
        num_coadd = integer(default=3)
    """

    def process(self, input):
        """
        Step for ramp fitting
        """
        # Load the input data model
        with RampModel(input) as input_model:

            # Vector of read times for all pixels
            input_times = input_model.times

            # Correct the nonlinearity
            if self.method.lower() == 'utr':
                slopes, slopes_err = fit_ramps_utr(input_times.astype(np.float32), input_model.data.astype(np.float32))
            elif self.method.lower() == 'mcds':
                slopes, slopes_err = fit_ramps_mcds(input_times.astype(np.float32), input_model.data.astype(np.float32), num_coadd=self.num_coadd)

        # Create 2D image model
        if input_model.meta.instrument.mode == 'IMG':
            model_result = ImagerModel(data=slopes, err=slopes_err, dq=np.all(input_model.dq, axis=(2, 3)))
        elif input_model.meta.instrument.mode == 'IFU':
            model_result = IFUImageModel(data=slopes, err=slopes_err, dq=np.all(input_model.dq, axis=(2, 3)))

        return model_result