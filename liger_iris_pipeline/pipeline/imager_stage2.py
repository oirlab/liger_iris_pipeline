#!/usr/bin/env python
from collections import defaultdict
import os.path as op

from jwst.associations.load_as_asn import LoadAsLevel2Asn

from liger_iris_pipeline import datamodels
from .base_pipeline import LigerIRISPipeline

from ..background import background_step
from ..dark_current import dark_current_step
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
        "bkg_subtract": background_step.BackgroundStep,
        "assign_wcs": assign_wcs_step.AssignWcsStep,
        "parse_subarray_map": parse_subarray_map_step.ParseSubarrayMapStep,
        "dark_current": dark_current_step.DarkCurrentStep,
        "flat_field": flat_field_step.FlatFieldStep,
        "photom": photom_step.PhotomStep,
        "resample": resample_step.ResampleStep,
    }

    # List of normal imaging exp_types
    image_exptypes = ["Liger_IMAGE", "IRIS_IMAGE"]

    def process(self, asn_filename : str):

        self.log.info("Starting ProcessImagerL2Pipeline ...")

        # Retrieve the input(s)
        asn = LoadAsLevel2Asn.load(asn_filename, basename=self.output_file)

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
            suffix = "cal"
            if isinstance(result, datamodels.IFUCubeModel):
                suffix = "calints"
            result.meta.filename = self.make_output_path(suffix=suffix)
            results.append(result)

        self.log.info("... ending ImagerStage2Pipeline")

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
                f"Wrong number of science files found in {exp_product['name']}"
            )
            self.log.warning("Using only first member.")
        science = science[0]

        self.log.info(f"Processing input {science} ...")
        if isinstance(science, datamodels.LigerIRISDataModel):
            input_model = science
        else:
            input_model = datamodels.open(science)

        # Record ASN pool and table names in output
        input_model.meta.asn.pool_name = pool_name
        input_model.meta.asn.table_name = asn_file

        # Do background processing, if necessary
        if len(members_by_type["background"]) > 0:

            # Setup for saving
            if self.bkg_subtract.suffix is None:
                self.bkg_subtract.suffix = "bsub"
            if isinstance(input_model, datamodels.IFUCubeModel):
                self.bkg_subtract.suffix = "bsubints"

            # Backwards compatibility
            if self.save_bsub:
                self.bkg_subtract.save_results = True

            # Call the background subtraction step
            input_model = self.bkg_subtract(input_model, members_by_type["background"])

        # Parse the subarray map
        input_model = self.parse_subarray_map(input_model)

        # Dark current subtraction
        input_model = self.dark_current(input_model)

        # Flat division
        input_model = self.flat_field(input_model)

        # Assign WCS
        input_model = self.assign_wcs(input_model)

        # Flux calibration
        input_model = self.photom(input_model)

        # Resample individual exposures, but only if it's one of the regular science image types.
        # NOTE: cls.image_exptypes needs updated
        if input_model.meta.exposure.type.upper() in self.image_exptypes:
            self.resample(input_model)

        # That's all folks
        self.log.info("Finished processing product {}".format(exp_product["name"]))

        # Return the processed model
        return input_model
