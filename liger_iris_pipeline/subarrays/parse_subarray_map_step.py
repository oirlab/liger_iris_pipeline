from ..stpipe.base_step import LigerIRISStep
from ..datamodels.dqflags import DQ_FLAGS

import numpy as np
import logging

logger = logging.getLogger(__name__)

__all__ = ["ParseSubarrayMapStep"]

class ParseSubarrayMapStep(LigerIRISStep):
    """
    TODO: Move most of this to the dedicated docs on subarrays.

    The step is only useful for full raw science frames which have been acquired concurrently with subarrays. This step parses the extension ``SUBARR_MAP`` and determines the parameters defining each specified subarray. These parameters are copied it into ImagerModel.meta.subarray_map, which is a ASDF-based property in the FITS file which encodes the metadata of the subarrays as a list of dictionaries.

    Each subarray is processed separately and the full science frame is also acquired and has missing values at the location of each of the subarrays (up to 10) which are currently being acquired.

    The raw science frame from the detector has a dedicated FITS extension that encodes the location of the subarrays, i.e. has zeros everywhere, then a rectangle of 1 at the location of subarray 1, a rectangle of 2 at the location of subarray 2 and so on. Subarrays cannot overlap.

    The locations of each subarray are determined with ``numpy.where`` from the extension ``SUBARR_MAP`` and are stored in the header as ``ImagerModel.meta.subarray_map``, which is a ASDF-based property in the FITS file which encodes the metadata of the subarrays as a list of dictionaries::

        ImagerModel.meta.subarray_map = [{"xstart":80, "ystart":70, "xsize":10, "ysize":10}, {"xstart":10, "ystart":20, "xsize":20, "ysize":20}]

    It also raises 1 bit of the data quality flag ``dq`` so that the algorithms which filter out bad data, e.g. when taking ``mean`` or ``median``, automatically filters them out. The bit used for that is ``SUBARRAY_DQ_BIT`` in ``parse_subarray_map_step.py``. (NOTE: Elaborate on this).

    Parameters
    ----------
    input : ImagerModel
        Input model to parse the subarray map from.

    Returns
    -------
    ImagerModel
        The input model with the subarray metadata parsed and set in ``model.subarray_map``.
    """

    class_alias = "parse_subarrays"

    def process(self, input):

        input_model = self.open_model(input)

        if "subarray_map" in input_model:
            
            logger.info("Parsing the SUBARRAY_MAP extension")
            
            result = input_model.copy()

            # Create metadata from image ID map
            for each in parse_subarray_map(result["subarray_map"]):
                result.meta.subarray_map.append(each)

            # Indicate subarrays in dq flags
            mask = result["subarray_map"] != 0
            result.dq[mask] = np.bitwise_or(
                result.dq[mask],
                DQ_FLAGS['SUBARRAY']
            )
        else:
            logger.info(f"No SUBARRAY_MAP extension found, skipping {self.class_alias} step")
            result = input_model
            self.skip = True

        return result

def parse_subarray_map(subarray_map : np.ndarray) -> list[dict]:
    """
    Parse a subarray map array into a list of subarray metadata dictionaries.

    Parameters
    ----------
    subarray_map : np.ndarray
        2D array where each unique non-zero value represents a subarray ID.
    
    Returns
    -------
    list[dict[str, np.ndarray]]
        List of dictionaries containing subarray metadata.
    """
    subarray_metadata = []
    subarr_ids = np.unique(subarray_map)
    for subarray_id in subarr_ids:
        if subarray_id == 0:
            continue
        subarray_indices = np.where(subarray_map == subarray_id)
        if len(subarray_indices[0]) == 0:
            break
        subarray_metadata.append(
            {
                "id": subarray_id,
                "xstart": int(subarray_indices[1][0] + 1),
                "ystart": int(subarray_indices[0][0] + 1),
                "xsize": int(subarray_indices[1][-1] - subarray_indices[1][0] + 1),
                "ysize": int(subarray_indices[0][-1] - subarray_indices[0][0] + 1),
                "detxsize": subarray_map.shape[1],
                "detysize": subarray_map.shape[0],
                "fastaxis": 0,
                "slowaxis": 1,
            }
        )
    return subarray_metadata