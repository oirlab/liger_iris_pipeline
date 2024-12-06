#! /usr/bin/env python

from ..base_step import LigerIRISStep

from ..datamodels import ImagerModel, RampModel
from ..drsrop_clib import uptheramp_c, mcds_c, nonlin_c
import numpy as np

# def utr(a):
#     return a


__all__ = ["ReadoutsampStep"]


class ReadoutsampStep(LigerIRISStep):
    """
    ReadoutsampStep:  Sampling
    """

    spec = """
        sigma = float(default=3.0)  # Clipping threshold
        maxiters = integer(default=None)  # Number of clipping iterations
        mode= string(default='utr')
    """

    def process(self, input):
        """
        Sampling step.
        Currently 3 Sampling modes
         -- CDS
         -- MCDS
         -- UTR
        """

        # Load the input data model
        with RampModel(input) as input_model:

            # Get the reference file names
            input_data = input_model.data[:, :, :, :].astype(np.int32)
            im_list = []
            for it in range(len(input_data)):
                ramp_data = input_data[it]
                num_reads = len(ramp_data)
                time_arr = np.arange(0, num_reads, 1).astype(np.int32)
                if self.mode == "mcds":
                    self.log.info("MCDS Sampling Selected")
                    result = mcds_c(ramp_data, time_arr, 2)
                else:
                    self.log.info("UTR Sampling Selected")
                    result = utr(ramp_data, time_arr, 2)
                im_list.append(result)
            result = np.sum(im_list, axis=0)
            print(result.shape)
            result = ImagerModel(data=result)
            result.update(input_model)

        return result
