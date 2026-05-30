from ..stpipe.base_step import LigerIRISStep
from .. import datamodels
import numpy as np
from ..datamodels.dqflags import DQ_FLAGS
from typing import Sequence


__all__ = ['MakeDetectorFlatStep']

COLD_FLAG =  DQ_FLAGS['COLD']

class MakeDetectorFlatStep(LigerIRISStep):
    """
    Create a detector flat calibration model from a combined rate map.
    This step expects the coadd step to have already been run on a list of flat field exposures.

    todo: add median white lamp intensity to metadata for instrument monitoring

    Parameters
    ----------
    input : L0Model
        Input flat field rate map to converted to detector flat calibration. Do not input a list.
    max_cores : int, optional
        Maximum number of CPU cores to use for parallel processing. Default is 1.
    cold_pixel_threshold : float, optional
        Threshold normalized flat value below which pixels are flagged as cold in the DQ array. Default is 0.9.

    Returns
    -------
    output : DetectorFlatModel
        The derived detector flat calibration model containing the normalized flat field map and updated DQ array.
    """

    spec = """
        cold_pixel_threshold = float(default=0.9) # Threshold to flag cold pixels in the detector flat field
    """

    class_alias = 'make_detflat'

    def process(self, input):
        if  isinstance(input, Sequence):
            raise ValueError("Rate maps must be combined before computing the detector flat. Input should not be a list.")

        input_model = self.open_model(input)
        
        # Define output model from inputs
        output_detflat = datamodels.DetectorFlatModel.from_datamodels(input_model)

        median_flat_whitelamp_intensity = np.nanmedian(input_model.data)

        # Median white lamp intensity for instrument monitoring
        # output_detflat.meta["MEDWLAMP"] = median_flat_whitelamp_intensity

        output_detflat.data = input_model.data / median_flat_whitelamp_intensity
        output_detflat.err = input_model.err / median_flat_whitelamp_intensity
        output_detflat.dq = input_model.dq.copy()
        _detect_cold_pixels(output_detflat.data, output_detflat.dq, self.cold_pixel_threshold)

        return output_detflat


def _detect_cold_pixels(flat_rate: np.ndarray, dq: np.ndarray, cold_pixel_threshold: float = 0.9):
    mask = flat_rate < cold_pixel_threshold
    dq[mask] |= COLD_FLAG