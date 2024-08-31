import numpy as np

from jwst.stpipe import Step
from jwst import datamodels

__all__ = ["MergeSubarraysStep"]


class MergeSubarraysStep(Step):
    """
    ParseSubarrayMapStep: Parse a subarray map
    extension, if available, and create header metadata
    and data quality flag accordingly.
    """

    def process(self, input):

        input = datamodels.open(input)

        # If single input, just return it
        if not isinstance(input, datamodels.ModelContainer):
            self.log.info("No subarray files provided, return the original model")
            return input
        else:
            input_models = input

        for model in input_models:
            if model.meta.subarray.id == 0:
                result = model.copy()
                break
        else:
            raise ValueError("Cannot identify the full frame, it should have SUBARRID=0")

        # Assume subarrays are in order
        for model in input_models:

            i_sub = model.meta.subarray.id

            # Skip the full frame
            if i_sub == 0:
                continue
            
            subarray_mask = result.subarr_map == i_sub

            # data
            result.data[subarray_mask] = input_models[i_sub].data.flatten()

            # dq
            result.dq[subarray_mask] = input_models[i_sub].dq.flatten()

            # err
            result.err[subarray_mask] = input_models[i_sub].err.flatten()

        return result
