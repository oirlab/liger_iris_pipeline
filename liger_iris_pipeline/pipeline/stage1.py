#!/usr/bin/env python
import logging
from collections import defaultdict
from .base_pipeline import LigerIRISPipeline
from liger_iris_pipeline import datamodels
from ..associations import L0Association

# step imports
from ..readout import NonlinearCorrectionStep, FitRampStep

__all__ = ['Stage1Pipeline']


class Stage1Pipeline(LigerIRISPipeline):
    """
    Stage 1 pipeline to process a series of raw reads to slope maps.
    
    Steps:
        NonlinCorrectionStep
        FitRampStep
    """

    default_association = L0Association

    # Define aliases to steps
    step_defs = {
        "nonlinear_correction": NonlinearCorrectionStep,
        "ramp_fit": FitRampStep,
    }

    # start the actual processing
    def process(self, input):
        #self.asn = self.input_to_asn(input)
        #self.log.info('Starting Stage 1 Pipeline ...')
        # Each exposure is a product in the association.
        # Process each exposure.
        # results = []
        # for product in self.asn.products:
        #     self.log.info(f"Processing product {input}")
        #     result = self.process_exposure_product(product)

        #     # Save result
        #     result.meta.filename = self.output_file
        #     results.append(result)

        # self.log.info("Stage1Pipeline completed")

        with datamodels.RampModel(input) as input_model:
            result = self.nonlinear_correction.run(input_model)
            result = self.ramp_fit.run(result)
        return result
    
    # Process each exposure
    def process_exposure_product(self, exp_product):
        """Process an exposure product.

        Parameters:
            exp_product (dict): The exposure product.
        """
        members_by_type = self.asn_product_by_types(exp_product)

        science = members_by_type["sci"][0]
        self.log.info(f"Processing input {science} ...")
        with datamodels.RampModel(science) as input_model:
            input_model = self.nonlinear_correction.run(input_model)
            output_model = self.ramp_fit.run(input_model)
        return output_model