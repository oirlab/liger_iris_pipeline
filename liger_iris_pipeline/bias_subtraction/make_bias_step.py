from ..stpipe.base_step import LigerIRISStep
from ..datamodels import DQ_FLAGS
import numpy as np
from typing import Sequence
from .. import datamodels
from ..jump_detection.jump_detection_difference import median_axis0_3d

from numba import njit, prange
from ..utils.parallelization_utils import numba_thread_scope

import logging

logger = logging.getLogger(__name__)

__all__ = ['MakeBiasStep']

UNRELIABLE_BIAS_FLAG =  DQ_FLAGS['UNRELIABLE_BIAS']
DO_NOT_USE_FLAG = DQ_FLAGS["DO_NOT_USE"]

class MakeBiasStep(LigerIRISStep):
    """
    Derive the detector bias and kTC noise from a set of dark exposures:

    1. Median combine the first read of each UTR cube to create the bias frame.
    2. Compute the kTC noise as the standard deviation across the first reads,
       using sigma-clipping to reject outliers.
    3. Flag pixels with high bias level or high kTC noise in the DQ array.

    Parameters
    ----------
    input : list
        List of input Ramp Models.
    max_cores : int, optional
        Maximum number of CPU cores to use for parallel processing.
        Default is 1.
    kTC_threshold : float, optional
        Threshold kTC above which pixels are flagged as bad in the DQ array.
        Default is 100 DN.
    bias_threshold : float, optional
        Threshold bias above which pixels are flagged as bad in the DQ array.
        Default is 1000 DN.

    Returns
    -------
    output : BiasModel
        The derived bias calibration model containing the
        bias frame, kTC noise map, and updated DQ array

    """

    spec = """
        kTC_threshold = float(default=100.0)
        bias_threshold = float(default=1000.0)
    """

    class_alias = 'make_bias'

    def process(self, input):

        # Normalize input to list of filepaths
        if isinstance(input, (datamodels.LigerIRISDataModel, str)):
            _input_list_tmp = [input]
        if  isinstance(input, Sequence):
            _input_list_tmp = input
        logger.info(f"Deriving the detector bias and kTC noise from {len(_input_list_tmp)} inputs.")

        # Open all input models
        input_models = [self.open_model(f) for f in _input_list_tmp]

        # Initialize outputs
        output_bias = datamodels.BiasModel.from_datamodels(input_models)

        # Ready bias arrays
        bias_arr = []
        for _input in input_models:
            bias_arr.append(_input.data[0,:,:])
        bias_arr = np.array(bias_arr)

        with numba_thread_scope(self.max_cores):

            # Compute bias as Median of first reads
            output_bias.data = median_axis0_3d(bias_arr)

            # Sigma clip on first reads to to compute kTC noise map
            output_bias.err = std_axis0_3d_sigclip(
                bias_arr,
                nsig=5, min_keep=10
            )

            # Output dq is just the copy of the first input
            # Bitwise reduce later if necessary.
            output_bias.dq = np.copy(input_models[0].dq)
            _find_bad_pixels_bias(
                output_bias.data, output_bias.err, output_bias.dq,
                kTC_threshold=self.kTC_threshold,
                bias_threshold=self.bias_threshold
            )

        # Data quality checks
        output_bias.meta.median_bias_level = np.nanmedian(output_bias.data)
        output_bias.meta.median_kTC_threshold = np.nanmedian(output_bias.err)

        # Return the output bias model
        return output_bias


@njit(nogil=True, parallel=True, cache=True)
def _find_bad_pixels_bias(
    bias: np.ndarray, kTC: np.ndarray, dq: np.ndarray,
    kTC_threshold: float = 100,
    bias_threshold: float = 1000
):
    ny, nx = bias.shape
    for j in prange(ny):
        for i in range(nx):
            if kTC[j, i] > kTC_threshold:
                dq[j, i] |= UNRELIABLE_BIAS_FLAG
            if bias[j, i] > bias_threshold:
                dq[j, i] |= UNRELIABLE_BIAS_FLAG

@njit(nogil=True, parallel=True, cache=True)
def std_axis0_3d_sigclip(bias_arr, nsig=5.0, min_keep=10):
    """
    Sigma-clipped std over axis=0 for bias_arr with shape (n_frames, ny, nx)

    Parameters
    ----------
    bias_arr : np.ndarray
        array (n_frames, ny, nx)
    nsig : float, optional
        sigma threshold. Default is 5.
    min_keep : int, optional
        minimum number of samples required after clipping. Default is 10.

    Returns
    -------
    std : np.ndarray
        (ny, nx) array
    """
    n_frames, ny, nx = bias_arr.shape
    std = np.zeros((ny, nx), dtype=bias_arr.dtype)

    for y in prange(ny):
        for x in range(nx):

            # ---------
            # Pass 1: initial mean/std (Welford)
            mean = 0.0
            M2 = 0.0
            count = 0

            for f in range(n_frames):
                v = bias_arr[f, y, x]
                count += 1
                delta = v - mean
                mean += delta / count
                M2 += delta * (v - mean)

            if count < 2:
                std[y, x] = 0.0
                continue

            sigma = np.sqrt(M2 / count)

            # ---------
            # Pass 2: sigma clipping + recompute stats
            mean2 = 0.0
            M2_2 = 0.0
            count2 = 0
            thresh = nsig * sigma

            for f in range(n_frames):
                v = bias_arr[f, y, x]
                if abs(v - mean) <= thresh:
                    count2 += 1
                    delta = v - mean2
                    mean2 += delta / count2
                    M2_2 += delta * (v - mean2)

            if count2 < min_keep:
                # fallback: unclipped std
                std[y, x] = sigma
            else:
                std[y, x] = np.sqrt(M2_2 / count2)

    return std