from ..stpipe.base_step import LigerIRISStep
from ..utils.subarray import get_subarray_model
from ..calibrations import BiasSelector
from ..utils.parallelization_utils import numba_thread_scope
from .. import datamodels

import numpy as np
from numba import njit, prange

import logging
logger = logging.getLogger(__name__)

__all__ = ['BiasSubtractionStep']


class BiasSubtractionStep(LigerIRISStep):
    """
    Performs bias subtraction by subtracting bias reference data from the input ramp model.

    The appropriate bias calibration is subtracted from the input data. 
    The input's ``err`` attribute is updated by adding the bias ``err`` attribute in quadarature.
    DQ flags are updated with bitwise or.

    Parameters
    ----------
    input : RampModel, str
        Input data.

    Calibrations
    ------------
    bias : BiasModel
    
    Returns
    -------
    RampModel
        The bias-subtracted science data model.
    """

    calibrations = {
        'bias' : {
            'selector' : BiasSelector,
            'selector_kwargs' : {}
        }
    }
    class_alias = 'bias_sub'

    def process(self, input):

        # Load the input model
        input_model = self.open_model(input)

        # Get output model
        if not isinstance(input_model, datamodels.ProcessedRampModel):
            output_model = datamodels.ProcessedRampModel.from_datamodels(
                input_model,
                include_data=True
            )
        else:
            output_model = input_model

        # Get the bias model
        bias_ref, _ = self.get_calibration(output_model, 'bias')
        logger.info(f'Using bias reference file: {bias_ref}')
        
        # Open the bias model and perform subtraction
        with self.open_model(bias_ref) as bias_model:
            
            # Get subarray model if needed
            bias_model_subarray = get_subarray_model(output_model, bias_model)

            # Subtract the bias
            subtract_bias(
                output_model.data,
                output_model.dq,
                bias_model_subarray.data,
                bias_model_subarray.dq,
                max_cores=self.max_cores
            )

        # Output
        return output_model


def subtract_bias(
    input_data : np.ndarray,
    input_dq : np.ndarray,
    bias_data : np.ndarray,
    bias_dq : np.ndarray,
    max_cores : int = 1
):
    """
    Subtract the bias from the ramps.

    Parameters
    ----------
    input_data
        Input ramp data with shape (Nreads, Ny, Nx).
    input_dq
        Input DQ array with shape (Ny, Nx).
    bias_data
        Bias data with shape (Ny, Nx).
    bias_dq
        Bias DQ array with shape (Ny, Nx).
    max_cores
        Maximum number of CPU cores to use.
    """
    with numba_thread_scope(max_cores):
        _bias_subtraction_numba(input_data, input_dq, bias_data, bias_dq)
    return input_data, input_dq


@njit(nogil=True, parallel=True, cache=True)
def _bias_subtraction_numba(data : np.ndarray, dq : np.ndarray, bias : np.ndarray, bias_dq : np.ndarray):
    n_read, ny, nx = data.shape
    for j in prange(ny):
        for i in range(nx):
            data[:, j, i] = data[:, j, i] - bias[j, i]
            dq[j, i] |= bias_dq[j, i]