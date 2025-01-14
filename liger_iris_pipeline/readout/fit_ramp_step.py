

from ..base_step import LigerIRISStep
from ..datamodels import RampModel, ImagerModel, IFUImageModel
from .fit_ramp_numba import fit_ramps_utr, fit_ramps_mcds

import copy
import numpy as np

__all__ = ["FitRampStep"]


class FitRampStep(LigerIRISStep):

    spec = """
        method = string(default='utr')  # Ramp fit method. Options are 'utr' and 'mcds'. For 'cds', use 'mcds' and set num_coadd to 1.
        num_coadd = integer(default=3) # The number of coadds for the 'mcds' method.
    """

    class_alias = "ramp_fit"

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
            model_result = ImagerModel(instrument=input_model.instrument, data=slopes, err=slopes_err, dq=np.all(input_model.dq, axis=(2, 3)))
        elif input_model.meta.instrument.mode == 'IFU':
            model_result = IFUImageModel(instrument=input_model.instrument, data=slopes, err=slopes_err, dq=np.all(input_model.dq, axis=(2, 3)))

        # TODO: Generalize the conversion from RampModel -> ImagerModel/IFUImageModel
        _meta = copy.deepcopy(input_model.meta.instance)
        _meta.update(input_model.meta.instance) # TODO: Check if this is the right way to merge the meta data
        model_result.meta = _meta
        model_result.meta.filename = None
        model_result.meta.data_level = 1
        model_result.meta.data_type = model_result.__class__.__name__
        self.status = "COMPLETE"

        return model_result