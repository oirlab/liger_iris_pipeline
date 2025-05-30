from ..base_step import LigerIRISStep
from ..datamodels import RampModel, ImagerModel, IFUImageModel
from .fit_ramp_numba import fit_ramps_ols, fit_ramps_mcds

import warnings
import copy
import numpy as np

__all__ = ["FitRampStep"]


class FitRampStep(LigerIRISStep):

    spec = """
        method = string(default='ols')  # Ramp fit method. Options are 'utr' and 'mcds'. For 'cds', use 'mcds' and set num_coadd to 1.
        num_coadd = integer(default=3) # The number of coadds for the 'mcds' method.
    """

    class_alias = "ramp_fit"

    def process(self, input):
        """
        Step for ramp fitting
        """
        # Load the input data model
        with self.open_model(input) as input_model:

            # Vector of read times for all pixels
            input_times = input_model.times

            # Correct the nonlinearity
            if self.method.lower() == 'ols':
                result = fit_ramps_ols(input_times.astype(np.float32), input_model.data.astype(np.float32))
            elif self.method.lower() == 'mcds':
                result = fit_ramps_mcds(input_times.astype(np.float32), input_model.data.astype(np.float32), num_coadd=self.num_coadd)
            elif self.method.lower() == 'cds':
                if self.num_coadd != 1:
                    warnings.warn(f"Using 'cds' method but num_coadd={self.num_coadd}. Ignoring.")
                result = fit_ramps_mcds(input_times.astype(np.float32), input_model.data.astype(np.float32), num_coadd=1)

        # TODO: Generalize the conversion from RampModel -> ImagerModel/IFUImageModel
        if input_model.meta.instrument.mode.lower() == 'img':
            model_result = ImagerModel(data=result[0], err=result[1], dq=np.all(input_model.dq, axis=(2, 3)))
        elif input_model.meta.instrument.mode.lower() in ('slicer', 'lenslet'):
            model_result = IFUImageModel(data=result[0], err=result[1], dq=np.all(input_model.dq, axis=(2, 3)))
        _meta = copy.deepcopy(input_model.meta.instance)
        _meta.update(input_model.meta.instance) # TODO: Check if this is the right way to merge the meta data
        model_result.meta = _meta
        model_result.meta.filename = None
        model_result.meta.data_level = 1
        self.status = "COMPLETE"

        return model_result