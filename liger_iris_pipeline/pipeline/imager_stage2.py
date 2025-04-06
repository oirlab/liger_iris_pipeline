#from ..associations import L1Association
from .base_pipeline import LigerIRISPipeline
from liger_iris_pipeline import datamodels
from ..parse_subarray_map import ParseSubarrayMapStep
from ..dark_subtraction import DarkSubtractionStep
from ..flat_field import FlatFieldStep
from ..assign_wcs import AssignWCSStep
from ..sky_subtraction import SkySubtractionImagerStep
#from jwst.photom import PhotomStep as JWSTPhotomStep
#from jwst.resample import ResampleStep as JWSTResampleStep

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

    #default_association = L1Association

    # Define alias to steps
    step_defs = {
        "parse_subarray_map": ParseSubarrayMapStep,
        "dark_sub": DarkSubtractionStep,
        "flat_field": FlatFieldStep,
        "sky_sub": SkySubtractionImagerStep,
        #"fluxcal": JWSTPhotomStep,
        "assign_wcs": AssignWCSStep,
        #"resample": JWSTResampleStep,
    }

    def process(self, input):

        # Each exposure is a product in the association.
        # Process each exposure.
        science = input["SCI"]
        with self.open_model(science) as input_model:
            input_model = self.parse_subarray_map.run(input_model)
            input_model = self.dark_sub.run(input_model)
            input_model = self.flat_field.run(input_model)
            if "SKY" in input:
                input_model = self.sky_sub.run(input_model, sky=input['SKY'])
            elif not self.sky_sub.skip:
                self.log.warning(f"No sky background found for {input_model} but {self.sky_sub.__class__.__name__}.skip=False. Skipping Sky Subtraction")

        input_model = self.assign_wcs.run(input_model)
        #input_model = self.fluxcal(input_model)

        # Update the data level
        input_model.meta.data_level = 2 # NOTE: Automate this somehow?

        return input_model