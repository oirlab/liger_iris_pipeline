#!/usr/bin/env python
from collections import defaultdict
import os.path as op

from jwst import datamodels
from jwst.associations.load_as_asn import LoadAsLevel2Asn
from jwst.stpipe import Pipeline

from ..dark_current import dark_current_step
from ..normalize import normalize_step


__all__ = ["ProcessFlatfieldL2"]


class ProcessFlatfieldL2(Pipeline):
    """
    ProcessFlatfieldL2: Remove dark and normalize exposure to create
    a flat field to be later added to the CRDS.

    Included steps are:
    dark_current, normalize
    """

    # Define alias to steps
    step_defs = {
        "dark_current": dark_current_step.DarkCurrentStep,
        "normalize": normalize_step.NormalizeStep,
    }

    def process(self, input):

        self.log.info("Starting preprocess flatfield ...")

        # Retrieve the input(s)
        asn = LoadAsLevel2Asn.load(input, basename=self.output_file)

        # Each exposure is a product in the association.
        # Process each exposure.
        results = []
        for product in asn["products"]:
            self.log.info("Processing product {}".format(product["name"]))
            if self.save_results:
                self.output_file = product["name"]
            try:
                getattr(asn, 'filename')
            except AttributeError:
                asn.filename = "singleton"
            result = self.process_exposure_product(
                product, asn["asn_pool"], op.basename(asn.filename)
            )

            # Save result
            suffix = "flat"
            result.meta.filename = self.make_output_path(suffix=suffix)
            results.append(result)

        self.log.info("... ending preprocess flatfield")

        self.output_use_model = True
        self.suffix = False
        return results

    # Process each exposure
    def process_exposure_product(self, exp_product, pool_name=" ", asn_file=" "):
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
        science = members_by_type["science"]
        if len(science) != 1:
            self.log.warning(
                "Wrong number of science files found in {}".format(exp_product["name"])
            )
            self.log.warning("    Using only first one.")
        science = science[0]

        self.log.info("Working on input %s ...", science)
        if isinstance(science, datamodels.JwstDataModel):
            input = science
        else:
            input = datamodels.open(science)

        # Record ASN pool and table names in output
        input.meta.asn.pool_name = pool_name
        input.meta.asn.table_name = asn_file
        input = self.dark_current(input)
        input = self.normalize(input)

        self.log.info("Finished processing product {}".format(exp_product["name"]))
        return input
