#!/usr/bin/env python
import logging
from collections import defaultdict
from .base_pipeline import LigerIRISPipeline
from liger_iris_pipeline import datamodels
from ..associations import IRISImagerL0Association

# step imports
from ..readout import fit_ramp_step
from ..readout import nonlincorr_step

__all__ = ['Stage1Pipeline']

# Define logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)


class Stage1Pipeline(LigerIRISPipeline):
    """
    Stage 1 pipeline to process a series of raw reads to slope maps.
    """

    spec = """
        save_calibrated_ramp = boolean(default=False)
    """

    # Define aliases to steps
    step_defs = {
        "nonlinear_correction": nonlincorr_step.NonlinCorrectionStep,
        "ramp_fit": fit_ramp_step.FitRampStep,
    }

    # start the actual processing
    def process(self, input):
        log.info('Starting Stage 1 Pipeline ...')
        if os.path.splitext(input)[1] == '.json':
            self.asn = IRISImagerL0Association.load(asn_file)
        else:
            self.asn = IRISImagerL0Association.from_member(input)
        # Each exposure is a product in the association.
        # Process each exposure.
        results = []
        for product in asn["products"]:
            self.log.info("Processing product {}".format(product["name"]))
            if self.save_results:
                self.output_file = product["name"]
            result = self.process_exposure_product(product)

            # Save result
            result.meta.filename = self.output_file
            results.append(result)

        self.log.info("Stage1Pipeline completed")

        self.output_use_model = True

        return results
    
    # Process each exposure
    def process_exposure_product(self, exp_product):
        """Process an exposure product.

        Parameters:
            exp_product (dict): The exposure product.
        """
        # Find all the member types in the product
        members_by_type = defaultdict(list)
        for member in exp_product["members"]:
            members_by_type[member["exptype"].lower()].append(member["expname"])

        science = members_by_type["science"][0]
        self.log.info(f"Processing input {science} ...")
        with datamodels.RampModel(science) as input_model:
            input_model = self.nonlinear_correction(input_model)
            output_model = self.ramp_fit(input_model)
        return output_model