import os
import copy

import liger_iris_pipeline.datamodels as datamodels
from .base_pipeline import LigerIRISPipeline
from ..dark_subtraction import DarkSubtractionStep
from ..normalize import NormalizeStep
from liger_iris_pipeline.associations import L1Association

__all__ = ["CreateFlatfield"]


class CreateFlatfield(LigerIRISPipeline):
    """
    Processes L1 flat field images to create a flat field reference file.

    Steps:
        dark_sub
        normalize
    """

    default_association = L1Association

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
    
    def get_output_dir(self, input_model : datamodels.LigerIRISDataModel):
        if self.output_dir is not None:
            return self.output_dir
        else:
            if input_model.filename is not None:
                return os.path.abspath(input_model.filename)
            else:
                return ''

    # Process each exposure
    def process_exposure_product(self, exp_product : dict):
        
        members_by_type = self.asn_product_by_types(exp_product)

        # Get the raw flat, assume only one for now.
        raw_flat_model = members_by_type["flat"][0]
        self.log.info(f"Processing {raw_flat_model}")
        input_model = datamodels.open(raw_flat_model)
        input_model = self.dark_sub.run(input_model)
        input_model = self.normalize.run(input_model)

        # To flat field model
        # TODO: Generalize the conversion from ImagerModel -> FlatModel
        flat_model = datamodels.FlatModel(
            data=input_model.data, err=input_model.err, dq=input_model.dq
        )
        _meta = copy.deepcopy(input_model.meta.instance)
        _meta.update(flat_model.meta.instance) # TODO: Check if this is the right way to merge the meta data
        flat_model.meta = _meta
        flat_model.meta.reftype = "FLAT"
        flat_model.meta.pedigree = None
        flat_model.meta.version = '0.0.1'
        flat_model.meta.filename = None
        flat_model.meta.data_type = flat_model.__class__.__name__

        self.log.info(f"Finished processing {members_by_type["flat"][0]}")

        return flat_model
