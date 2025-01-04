import liger_iris_pipeline.datamodels as datamodels
from .base_pipeline import LigerIRISPipeline
from ..dark_subtraction import DarkSubtractionStep
from ..normalize import NormalizeStep
from liger_iris_pipeline.associations import ImagerL1Association

__all__ = ["CreateFlatfield"]


class CreateFlatfield(LigerIRISPipeline):
    """
    Processes L1 flat field images to create a flat field reference file.

    Steps:
        dark_sub
        normalize
    """

    # TODO: MAKE THIS GENERIC FOR IMAGER AND IFU DETECTORS
    default_association = ImagerL1Association

    # Define alias to steps
    step_defs = {
        "dark_sub": DarkSubtractionStep,
        "normalize": NormalizeStep,
    }

    def process(self, input):

        self.log.info("Starting Create flatfield ...")

        # Load the association
        self.asn = self.input_to_asn(input)
        
        # Each exposure is a product in the association.
        # Process each exposure.
        result = self.process_exposure_product(self.asn.products[0])
        self.log.info("Finished Create Flatfield.")
        return result

    # Process each exposure
    def process_exposure_product(self, exp_product : dict):
        
        members_by_type = self.asn_product_by_types(exp_product)

        # Get the raw flat, assume only one for now.
        raw_flat_model = members_by_type["flat"][0]
        self.log.info(f"Processing {raw_flat_model}")
        input_model = datamodels.open(raw_flat_model)
        input_model = self.dark_sub(input_model)
        input_model = self.normalize(input_model)

        # To flat field model
        flat_model = datamodels.FlatModel.from_model(input_model)
    
        # Save the results
        if self.save_results:
            output_file = datamodels.ReferenceFileModel.generate_filename(
                instrument=flat_model.instrument, detector=flat_model.meta.instrument.detector,
                reftype='FLAT', date=flat_model.meta.date, version='0.0.1'
            )
            flat_model.save(output_file)
            self.log.info(f"Saved {flat_model}")

        self.log.info(f"Finished processing {exp_product['name']}")

        return flat_model
