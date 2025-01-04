from ..associations import ImagerL1Association
from .base_pipeline import LigerIRISPipeline
from liger_iris_pipeline import datamodels
from ..parse_subarray_map import ParseSubarrayMapStep
from ..dark_subtraction import DarkSubtractionStep
from ..flatfield import FlatFieldStep
from ..assign_wcs import AssignWCSStep
from ..sky_subtraction import SkySubtractionImagerStep
from jwst.photom import PhotomStep as JWSTPhotomStep
from jwst.resample import ResampleStep as JWSTResampleStep

__all__ = ["ImagerStage2Pipeline"]


class ImagerStage2Pipeline(LigerIRISPipeline):
    
    """
    Standard pipeline for processing Liger and IRIS Imager data from L1 to L2.
    
    Steps:
        ParseSubarrayMapStep
        DarkSubtractionStep
        FlatFieldStep
        SkySubtractionImagerStep
        AssignWCSStep
        PhotomStep (JWST)
        ResampleStep (JWST)
    """

    default_association = ImagerL1Association

    # Define alias to steps
    step_defs = {
        "parse_subarray_map": ParseSubarrayMapStep,
        "dark_sub": DarkSubtractionStep,
        "flat_field": FlatFieldStep,
        "sky_sub": SkySubtractionImagerStep,
        "photom": JWSTPhotomStep,
        "assign_wcs": AssignWCSStep,
        "resample": JWSTResampleStep,
    }

    def process(self, input):

        # Load the association
        self.asn = self.input_to_asn(input)

        self.log.info(f"Starting ImagerStage2Pipeline ...")

        # Each exposure is a product in the association.
        # Process each exposure.
        results = []
        for product in self.asn["products"]:
            result = self.process_exposure_product(product)

            # Save result
            result.meta.filename = self.output_file
            results.append(result)

        self.log.info("ImagerStage2Pipeline completed")

        return results
    
    # Process each exposure
    def process_exposure_product(self, exp_product : dict):
        """Process an exposure product.

        Parameters:w
            exp_product (dict): The exposure product.
        """

        # Members by type
        members_by_type = self.asn_product_by_types(exp_product)

        # Get the science member. Assumes only one
        # TODO: Enforce one science exposure per product in Association class
        science = members_by_type["sci"][0]

        self.log.info(f"Processing {science}")
        input_model = datamodels.open(science)

        # Run remaining steps
        input_model = self.parse_subarray_map(input_model)
        input_model = self.dark_sub(input_model)
        input_model = self.flat_field(input_model)
        if len(members_by_type["sky"]) > 0:
            input_model = self.sky_sub(input_model, members_by_type["sky"][0])
        elif not self.sky_sub.skip:
            self.log.warning(f"No sky background found for {input_model} but {self.sky_sub.__class__.__name__}.skip=False.")

        input_model = self.assign_wcs(input_model)
        input_model = self.photom(input_model)

        self.log.info(f"Finished processing {input_model}")

        return input_model
