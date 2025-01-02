#!/usr/bin/env python
from collections import defaultdict
import os.path

import liger_iris_pipeline.datamodels as datamodels
from .base_pipeline import LigerIRISPipeline
from ..dark_subtraction import dark_step
from ..normalize import normalize_step
from liger_iris_pipeline.associations import IRISImagerL1Association


__all__ = ["CreateFlatfield"]


class CreateFlatfield(LigerIRISPipeline):
    """
    ProcessFlatfield: Remove dark and normalize exposure to create
    a flat field to be later added to the CRDS.

    Included steps are:
    dark_current, normalize
    """

    # Define alias to steps
    step_defs = {
        "dark_sub": dark_step.DarkSubtractionStep,
        "normalize": normalize_step.NormalizeStep,
    }

    def process(self, input):

        self.log.info("Starting Create flatfield ...")

        # Load the association
        if os.path.splitext(input)[1] == '.json':
            asn = IRISImagerL1Association.load(input)
        else:
            asn = IRISImagerL1Association.from_product(input)

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

        self.log.info("... ending Process flatfield")

        self.output_use_model = True
        self.suffix = False
        return results

    # Process each exposure
    def process_exposure_product(self, exp_product):
        """Process an exposure found in the association product

        Parameters
        ----------
        exp_product: dict
            A Level2b association product.

        pool_name: str
            The pool file name. Used for recording purposes only.

        asn_file: str
            The name of the association file.
            Used for recording purposes only.
        """
        # Find all the member types in the product
        members_by_type = defaultdict(list)
        for member in exp_product["members"]:
            members_by_type[member["exptype"].lower()].append(member["expname"])

        # Get the science member. Technically there should only be
        # one. We'll just get the first one found.
        flat = members_by_type["flat"][0]

        self.log.info("Working on input %s ...", flat)
        data = datamodels.open(flat)

        # Record ASN pool and table names in output
        data = self.dark_sub(data)
        data = self.normalize(data)

        self.log.info(f"Finished processing product {exp_product['name']}")
        return data
