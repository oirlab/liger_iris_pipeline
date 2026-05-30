from ..stpipe.base_step import LigerIRISStep
from .. import datamodels

import numpy as np
import scipy.stats
import logging

logger = logging.getLogger(__name__)

__all__ = ["NormalizeStep"]


class NormalizeStep(LigerIRISStep):
    """
    Normalize a frame by dividing by its own mean, median, or mode.

    The normalization factor is computed as either the mean, median, or mode of the data. This value is then divided into the data model's ``data``  and ``err`` attributes.

    Parameters
    ----------
    input : ImagerModel or IFSImageModel
        Input model to normalize.
    method : str
        Normalization method - 'median', 'mean', or 'mode'.
        Default is 'median'.
    
    Returns
    -------
    output
        The normalized frame (same type as input).
    """

    class_alias = "normalize"

    spec = """
        method = string(default='median')
    """

    def process(self, input):
        input_model = self.open_model(input)
        logger.info(f"Running normalize with method {self.method}")
        result = normalize_data(input_model, method=self.method)
        return result

def normalize_data(input_model : datamodels.LigerIRISDataModel, method : str):
    """
    Divides the input frame by its own median, mean, or mode
    based on the method string.

    Parameters
    ----------
    input_model: LigerIRISDataModel
        The input data to normalize. Can be either 2D or 3D.
    method: str
        Method to use:
            - median (default) uses `numpy.median`
            - mean uses `numpy.mean`
            - mode uses `scipy.stats.mode`

    Returns
    -------
    output: LigerIRISDataModel
        The Normalized data model

    """

    # Create a mask for valid pixels (where DQ == 0)
    mask = input_model.dq == 0

    # Determine normalization factor
    if method is None:
        norm_factor = 1
    elif method == "mean":
        norm_factor = np.mean(input_model.data[mask])
    elif method == "median":
        norm_factor = np.median(input_model.data[mask])
    elif method == "mode":
        norm_factor = scipy.stats.mode(input_model.data[mask], axis=None).mode
    else:
        raise ValueError(f"Unknown normalization method: {method}")

    # Apply normalization to data and error arrays
    input_model.data /= norm_factor

    if hasattr(input_model, 'err'):
        input_model.err /= norm_factor
    if hasattr(input_model, 'var_poisson'):
        input_model.var_poisson /= norm_factor**2
    if hasattr(input_model, 'var_rnoise'):
        input_model.var_rnoise /= norm_factor**2

    return input_model