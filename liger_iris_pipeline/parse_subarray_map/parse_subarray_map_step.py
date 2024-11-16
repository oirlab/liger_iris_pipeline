import numpy as np

from ..base_step import LigerIRISStep
from .. import datamodels

__all__ = ["ParseSubarrayMapStep"]

SUBARRAY_DQ_BIT = 4

# NOTE: xstart/ystart use 1-based indexing
def parse_subarray_map(subarray_map):
    subarray_metadata = []
    for subarray_id in range(1, 10 + 1):
        subarray_indices = np.where(subarray_map == subarray_id)
        if len(subarray_indices[0]) == 0:
            break
        subarray_metadata.append(
            {
                "xstart": int(subarray_indices[1][0] + 1),
                "ystart": int(subarray_indices[0][0] + 1),
                "xsize": int(subarray_indices[1][-1] - subarray_indices[1][0] + 1),
                "ysize": int(subarray_indices[0][-1] - subarray_indices[0][0] + 1),
            }
        )
    return subarray_metadata


class ParseSubarrayMapStep(Step):
    """
    ParseSubarrayMapStep: Parse a subarray map
    extension, if available, and create header metadata
    and data quality flag accordingly
    """

    def process(self, input):

        if isinstance(input, str):
            input_model = datamodels.open(input)
        else:
            input_model = input

        if "subarr_map" in input_model:
            
            self.log.info("Parsing the SUBARR_MAP extension")
            
            result = input_model.copy()

            # Create metadata from image ID map
            for each in parse_subarray_map(result["subarr_map"]):
                result.meta.subarray_map.append(each)

            # Indicate subarrays in dq flags
            result.dq[result["subarr_map"] != 0] = np.bitwise_or(
                result.dq[result["subarr_map"] != 0],
                2 ** SUBARRAY_DQ_BIT
            )
        else:
            self.log.info("No SUBARR_MAP extension found")
            result = input_model

        return result
