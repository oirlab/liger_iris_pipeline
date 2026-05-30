from ..stpipe.base_step import LigerIRISStep
from .. import datamodels
from ..datamodels.dqflags import DQ_FLAGS

from numba import njit, prange
from typing import Sequence
from copy import copy
import numpy as np

__all__ = ['MakeDarkStep']

HOT_FLAG =  DQ_FLAGS['HOT']

class MakeDarkStep(LigerIRISStep):
    """
    Create a dark calibration model from a combined rate map.
    This step expects the coadd step to have already been run on a list of darks exposures.
    Hot pixels are flagged in the DQ array based on a provided threshold.

    Parameters
    ----------
    input : ImagerModel or IFSImageModel
        Input rate map exposures.
    max_cores : int, optional
        Maximum number of CPU cores to use for parallel processing.
        Default is 1.
    hot_pixel_threshold : float, optional
        Threshold dark rate above which pixels are flagged as hot in the DQ array.
        Default is 5 e-/s.

    Returns
    -------
    DarkModel
        The derived dark calibration model.
    """

    spec = """
        hot_pixel_threshold = float(default=5.0)
    """

    class_alias = 'make_dark'

    def process(self, input):
        if  isinstance(input, Sequence):
            raise ValueError("Rate maps must be combined before computing the detector dark. Input should not be a list.")

        # Open input model
        input_model = self.open_model(input)
        
        # Define output model from inputs
        output_dark = datamodels.DarkModel.from_datamodels(input_model)

        # Median dark rate for instrument monitoring
        output_dark.meta.median_dark_level = np.nanmedian(input_model.data)

        # Populate data attributes
        output_dark.data = input_model.data
        output_dark.err = input_model.err
        output_dark.dq = np.copy(input_model.dq)

        # Flag hot pixels
        _detect_hot_pixels(
            output_dark.data, output_dark.dq,
            hot_pixel_threshold=self.hot_pixel_threshold
        )

        return output_dark


@njit(nogil=True, parallel=True, cache=True)
def _detect_hot_pixels(
    dark_rate: np.ndarray, dq: np.ndarray,
    hot_pixel_threshold: float = 0.9
):
    ny, nx = dark_rate.shape
    for j in prange(ny):
        for i in range(nx):
            if dark_rate[j, i] > hot_pixel_threshold:
                dq[j, i] |= HOT_FLAG