from .base_pipeline import LigerIRISPipeline
from liger_iris_pipeline import datamodels
from ..parse_subarray_map import ParseSubarrayMapStep
from ..dark_subtraction import DarkSubtractionStep
from ..flat_field import FlatFieldStep
from ..assign_wcs import AssignWCSStep
from ..background import CalculateBackgroundImagerStep, SubtractBackgroundImagerStep
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

    # Define alias to steps
    step_defs = {
        "parse_subarray_map": ParseSubarrayMapStep,
        "dark_sub": DarkSubtractionStep,
        "flat_field": FlatFieldStep,
        "calc_background": CalculateBackgroundImagerStep,
        "background_sub": SubtractBackgroundImagerStep,
        "assign_wcs": AssignWCSStep,
    }

    def process(self, input : dict) -> dict:

        # Correct dark and flat
        sci_models = []
        for sci in input['SCI']:
            sci_model = self.parse_subarray_map.run(sci)
            sci_model = self.dark_sub.run(sci_model)
            sci_model = self.flat_field.run(sci_model)
            sci_models.append(sci_model)
        
        # Calculate the background from the science or sky data
        if not self.calc_background.skip:
            if 'SKY' in input and len(input['SKY']) > 0:
                sky_models = []
                for sky in input['SKY']:
                    sky_model = self.parse_subarray_map.run(sky)
                    sky_model = self.dark_sub.run(sky_model)
                    sky_model = self.flat_field.run(sky_model)
                    sky_models.append(sky_model)
                self.background = self.calc_background.run(sky_models)
            else:
                self.background = self.calc_background.run(sci_models)
        else:
            self.background = None
            self.calc_background.on_skip()

        # Subtract the background from each science model
        for i in range(len(sci_models)):
            sci_models[i] = self.background_sub.run(sci_models[i], background=self.background)

        # Assign the WCS to each science model
        for i in range(len(sci_models)):
            sci_models[i] = self.assign_wcs.run(sci_models[i])

        # Flux calibrate each science model
        # NOTE: Commenting this out until we implement flux calibration step
        #for i in range(len(sci_models)):
        #    sci_models[i] = self.flux_cal.run(sci_models[i])

        # Save the science models
        for sci_model in sci_models:
            sci_model.meta.data_level = 2 # NOTE: Automate this somehow?
            if self.save_results: # NOTE: Use HISPEC approach to manage saving results
                sci_model.save(output_dir=self.ouptut_dir)

        # Return the list of science models
        return sci_models