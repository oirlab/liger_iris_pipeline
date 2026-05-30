from ..stpipe.base_step import LigerIRISStep
from .. import datamodels

import numpy as np

__all__ = ["MergeSubarraysStep"]


class MergeSubarraysStep(LigerIRISStep):
    """
    Merges a set of individual subarrays into a full frame image. This is a level 3 tool; it assumes the inputs have been already processed by the appropriate Stage 2 Pipeline.

    Currently the algorithm is trivial, it only puts back the relevant slices of the ``data``, ``dq`` and ``err`` extensions in the correct location without any modifications.

    Parameters
    ----------
    input : ImagerModel, str
        Input data.
    
    Returns
    -------
    ImagerModel
        The merged full frame.
    """

    class_alias = "merge_subarrays"

    def process(self, input):

        # If single input, just return it
        # if not isinstance(input, L1Association):
        #     self.log.info("No subarray files provided, return the original model")
        #     return input
        
        # Load the association
        self.asn = self.input_to_asn(input)

        for member in self.asn.products[0]['members']:
            with datamodels.open(member['expname']) as input_model:
                if input_model.meta.subarray.id == 0:
                    result = input_model.copy()
                    break
        else:
            raise ValueError("Cannot identify the full frame, it should have SUBARRID=0")

        # Assume subarrays are in order
        for member in self.asn.products[0]['members']:

            with datamodels.open(member['expname']) as model:

                i_sub = model.meta.subarray.id

                # Skip the full frame
                if i_sub == 0:
                    continue
                
                subarray_mask = result.subarr_map == i_sub

                # data
                result.data[subarray_mask] = model.data.flatten()

                # dq
                result.dq[subarray_mask] = model.dq.flatten()

                # err
                result.err[subarray_mask] = model.err.flatten()

        return result
