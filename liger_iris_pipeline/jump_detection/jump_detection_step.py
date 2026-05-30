from ..stpipe.base_step import LigerIRISStep
from ..jump_detection.jump_detection_difference import jump_detection_difference
from .jump_detection_jwst import jump_detection_jwst
from ..calibrations import GainSelector, ReadNoiseSelector
from .. import datamodels

from ..utils.subarray import get_subarray_model

import logging

logger = logging.getLogger(__name__)

__all__ = ['JumpDetectionStep']


class JumpDetectionStep(LigerIRISStep):
    """
    Flags jumps in the up-the-ramp data.

    Parameters
    ----------
    input : RampModel
        Input ramp model to perform jump detection on.
    method : str
        Jump detection method. Options are 'JWST' and 'TPD'. Default is 'JWST'.
    rejection_threshold : float
        Rejection sigma-threshold for jump detection. Default is 4.0.
    max_cores : int, optional
        Maximum number of CPU cores to use.
        Default is 1.

    Calibrations
    ------------
    gain : `GainModel` - Selector: `GainSelector`
    rn : `ReadNoiseModel` - Selector: `ReadNoiseSelector`

    Returns
    -------
    output : RampModel
        The input ramp model with the DQ flags updated to indicate detected jumps.
    """

    spec = """
        method = string(default = "TPD")  # Jump detection method: 'JWST' or 'TPD'
        rejection_threshold = float(default = 4.0)  # Rejection sigma-threshold for jump detection
        max_cores = integer(default = 1)  # Maximum number of CPU cores to use
    """

    calibrations = {
        'gain' : {
            'selector' : GainSelector,
            'selector_kwargs' : {}
        },
        'rn' : {
            'selector' : ReadNoiseSelector,
            'selector_kwargs' : {}
        }
    }
    class_alias = "jump_detection"

    def process(self, input):

        # Open the input data model
        input_model = self.open_model(input)
        n_reads = input_model.data.shape[0]

        # Get output model
        if not isinstance(input_model, datamodels.ProcessedRampModel):
            output_model = datamodels.ProcessedRampModel.from_datamodels(
                input_model,
                include_data=True
            )
        else:
            output_model = input_model

        # Skip if not enough reads
        if n_reads <= 2:
            logger.warning(f"Not enough reads available for jump detection ({n_reads}), skipping.")
            self._status = 'SKIPPED'
            return input_model

        logger.info(f"Finding jumps with method={self.method.lower()}")

        # Perform jump detection - this only modifies the DQ mask
        if self.method.lower() == 'jwst':
            logger.info(
                "JWST jump detection is not optimized with shared memory here.",
                "For a shared memory execution, "
                "set the flag jwst_jump_detection=True in the ramp fitting step and run jump detection from there."
                "Although shared memory only works with JWST ramp fitting methods."
            )
            jump_detection_jwst(
                input_model.data,
                input_model.dq_raw,
                input_model.dq,
                #max_cores=self.max_cores,
                rejection_threshold=self.rejection_threshold
            )
        elif self.method.lower() == 'tpd':
            
            # Get the gain and read noise reference files
            gain_ref, _ = self.get_calibration(output_model, "gain")
            logger.info(f"Using gain reference {gain_ref}")

            rn_ref, _ = self.get_calibration(output_model, "rn")
            logger.info(f"Using read noise reference {rn_ref}")
            
            # Open the gain and read noise reference files
            with self.open_model(gain_ref) as gain_model \
                , self.open_model(rn_ref) as rn_model:

                # Get subarray models if needed
                gain_model_subarray = get_subarray_model(output_model, gain_model)
                rn_model_subarray = get_subarray_model(output_model, rn_model)
                # Perform jump detection
                jump_detection_difference(
                    output_model.data,
                    output_model.dq_raw,
                    output_model.dq,
                    rdnoise=rn_model_subarray.rn,
                    gain=gain_model_subarray.gain,
                    max_cores=self.max_cores,
                    rejection_threshold=self.rejection_threshold
                )
        else:
            logger.error(f"Invalid jump detection method {self.method.lower()}")
            raise ValueError(f"Invalid jump detection method {self.method.lower()}")

        # Output
        return output_model