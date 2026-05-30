from .. import datamodels
from ..stpipe.base_pipeline import LigerIRISPipeline
from ..dq_init import DQInitStep
from ..bias_subtraction.make_bias_step import MakeBiasStep
from typing import Sequence

import logging
logger = logging.getLogger(__name__)


__all__ = ['ProcessBiasPipeline']


class ProcessBiasPipeline(LigerIRISPipeline):
    """
    Pipeline to process a set of dark UTR ramps and create a bias calibration.

    **Input:** A list of RampModels all containing dark exposures.

    Steps
    -----
    - ``dq_init`` - `DQInitStep`
    - ``make_bias`` - `MakeBiasStep`

    Returns
    -------
    BiasModel
        The derived bias calibration model.

    """

    # Define alias to steps
    step_defs = {
        "dq_init" : DQInitStep,
        "make_bias" : MakeBiasStep,
    }

    class_alias = "process_bias"

    def process(self, input):
        
        # Convert input to list
        if isinstance(input, (datamodels.LigerIRISDataModel, str)):
            input_list = [input]
        if isinstance(input, Sequence):
            input_list = input

        # Store all results in a list
        results = []

        # Initial log
        logger.info(f"Using {len(input_list)} inputs.")

        # Loop over each UTR cube
        for k, _input in enumerate(input_list):

            # Apply DQ init to each UTR cube
            logger.info(f"Processing input {k+1}/{len(input_list)}: {_input}")
            model_to_process = self.open_model(_input)
            _result = self.dq_init.run(model_to_process)
            results.append(_result)

        # Coadd the first reads of all UTR cubes to create the bias calibration
        bias_result = self.make_bias.run(results)

        # Register the detector gain calibration to the calibration database
        # self.register_bias_cal.run(bias_result)

        # Store results for potential use in later steps or for debugging
        self.results = results

        # Return the final bias calibration result
        return bias_result