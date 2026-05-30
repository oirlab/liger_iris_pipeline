from ..stpipe.base_step import LigerIRISStep
from ..datamodels.dqflags import DQ_FLAGS
import numpy as np
from copy import copy
from typing import Sequence
from .. import datamodels
from ..jump_detection.jump_detection_difference import median_axis0_3d

from numba import njit, prange
from ..utils.parallelization_utils import numba_thread_scope

import logging
logger = logging.getLogger(__name__)

__all__ = ['MakeSaturationStep']


class MakeSaturationStep(LigerIRISStep):
    """
    Create a saturation calibration model from a list of raw ramp exposures.
    
    The saturation threshold is determined by taking the median of the
    last reads of a list of raw ramp exposures.

    Parameters
    ----------
    input : Sequence of RampModel
        A list of raw ramp exposures to use for deriving the saturation threshold.
    offset : float, optional
        Value to subtract from the last read median to define the saturation threshold.
        This can help account for read noise or other systematics.
        Default is 100.
    max_cores : int, optional
        Maximum number of CPU cores to use.
        Default is 1.

    Returns
    -------
    output : `SaturationModel`
        The derived saturation calibration model containing the per-pixel saturation thresholds.

    """

    spec = """
        max_cores = integer(default=1)   # Maximum number of CPU cores to use
        offset = float(default=100)  # Offset to subtract from last read median
        suffix = string(default='')
    """

    class_alias = "make_sat"

    def process(self, input):
        if isinstance(input, (datamodels.LigerIRISDataModel, str)):
            _input_list_tmp = [input]
        if  isinstance(input, Sequence):
            _input_list_tmp = input
        nfiles = len(_input_list_tmp)
        logger.info(f"Deriving the detector saturation threshold by taking the median of the last reads of a list of {nfiles} inputs.")

        input_models = [self.open_model(f) for f in _input_list_tmp]

        # Define output model from inputs
        output_saturation = datamodels.SaturationModel.from_datamodels(input_models)

        last_read_arr = []
        for _input in input_models:
            last_read_arr.append(_input.data[-1, :, :])
        last_read_arr = np.array(last_read_arr)

        with numba_thread_scope(self.max_cores):
            output_saturation.sat_thresh = median_axis0_3d(last_read_arr) - self.offset

        # Output
        return output_saturation