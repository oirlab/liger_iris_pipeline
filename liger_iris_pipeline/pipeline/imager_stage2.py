#!/usr/bin/env python
from collections import defaultdict
import os
import json

from liger_iris_pipeline import datamodels
from ..associations import IRISImagerL1Association
from .base_pipeline import LigerIRISPipeline

from ..sky_subtraction import sky_subtraction_imager_step
from ..dark_subtraction import dark_step
from jwst.assign_wcs import assign_wcs_step
from ..flatfield import flat_field_step
from ..parse_subarray_map import parse_subarray_map_step
from jwst.photom import photom_step
from jwst.resample import resample_step

__all__ = ["ImagerStage2Pipeline"]


class ImagerStage2Pipeline(LigerIRISPipeline):
    """
    Included steps are:
    background_subtraction, assign_wcs, flat_field, photom and resample.
    """

    spec = """
        save_bsub = boolean(default=False) # Save background-subracted science
    """

    # Define alias to steps
    step_defs = {
        "parse_subarray_map": parse_subarray_map_step.ParseSubarrayMapStep,
        "dark_sub": dark_step.DarkSubtractionStep,
        "flat_field": flat_field_step.FlatFieldStep,
        "sky_sub": sky_subtraction_imager_step.SkySubtractionImagerStep,
        "photom": photom_step.PhotomStep,
        "assign_wcs": assign_wcs_step.AssignWcsStep,
        "resample": resample_step.ResampleStep,
    }

    def process(self, input):

        # Load the association
        if os.path.splitext(input)[1] == '.json':
            asn = IRISImagerL1Association.load(input)
        else:
            asn = IRISImagerL1Association.from_product(input)
        
        self.log.info("Starting ImagerStage2Pipeline ...")

        # Each exposure is a product in the association.
        # Process each exposure.
        results = []
        for product in asn["products"]:
            self.log.info(f"Processing product {product['name']}")
            if self.save_results:
                self.output_file = product["name"]
            result = self.process_exposure_product(product)

            # Save result
            result.meta.filename = self.output_file
            results.append(result)

        self.log.info("ImagerStage2Pipeline completed")

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

        # Get the science member. Technically there should only be
        # one. We'll just get the first one found.
        science = members_by_type["science"]
        if len(science) != 1:
            self.log.warning(f"Wrong number of science files found in {exp_product['name']}")
            self.log.warning("Using only first member.")
        science = science[0]

        self.log.info(f"Processing input {science} ...")
        input_model = datamodels.open(science)

        # Run remaining steps
        input_model = self.parse_subarray_map(input_model)
        input_model = self.dark_sub(input_model)
        input_model = self.flat_field(input_model)
        if len(members_by_type["sky"]) > 0:
            input_model = self.sky_sub(input_model, members_by_type["sky"][0])
        input_model = self.assign_wcs(input_model)
        input_model = self.photom(input_model)

        self.log.info(f"Finished processing product {exp_product['name']}")

        return input_model
