#! /usr/bin/env python

from ..step import Step
from ..datamodels import RampModel
from ..drsrop_clib import uptheramp_c, mcds_c, nonlin_c
import numpy as np
from astropy.io import fits

__all__ = ["NonlincorrStep"]


class NonlincorrStep(Step):
    """
    ReadoutsampStep:  Sampling
    """

    spec = """
        sigma = float(default=3.0)  # Clipping threshold
        maxiters = integer(default=None)  # Number of clipping iterations
    """
    reference_file_types = ["nonlincoeff"]

    def process(self, input):
        """
        Step for Nonlinearity Correction
        """

        # Load the input data model
        with RampModel(input) as input_model:
            nonlin_coeff_file = self.get_reference_file(input_model, "nonlincoeff")
            nonlin_coeff_data = fits.getdata(nonlin_coeff_file).astype(np.float32)
            c0 = nonlin_coeff_data[0]
            c1 = nonlin_coeff_data[1]
            c2 = nonlin_coeff_data[2]
            c3 = nonlin_coeff_data[3]
            c4 = nonlin_coeff_data[4]
            # Get the reference file names
            input_data = input_model.data[:, :, :, :].astype(np.int32)
            ramp_list = []
            for it in range(len(input_data)):
                ramp_data = input_data[it]
                num_reads = len(ramp_data)
                time_arr = np.arange(0, num_reads, 1).astype(np.int32)
                result = nonlin_c(ramp_data, time_arr, c0, c1, c2, c3, c4)
                result = result.astype(np.int32)
                ramp_list.append(result)
            # result = uptheramp_c(result,time_arr)
            output_data = np.array(ramp_list).astype(np.int32)
            result = RampModel(data=output_data)
            result.update(input_model)

        return result
