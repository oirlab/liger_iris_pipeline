from ..stpipe.base_pipeline import LigerIRISPipeline
from liger_iris_pipeline import datamodels
from ..subarrays import ParseSubarrayMapStep
from ..dark_subtraction import DarkSubtractionStep
from ..detector_flat import DetectorFlatStep
from ..assign_wcs import AssignWCSStep
from ..background import CalculateBackgroundImagerStep, BackgroundSubtractionImagerStep
from ..gain import GainStep

__all__ = ["Stage2ImagerPipeline"]


class Stage2ImagerPipeline(LigerIRISPipeline):
    
    """
    Standard pipeline for processing Liger and IRIS Imager data from L1 to L2.

    Steps
    -----
    - ``parse_subarrays`` - `ParseSubarrayMapStep`
    - ``dark_sub`` - `DarkSubtractionStep`
    - ``gain_corr`` - `GainStep`
    - ``detflat`` - `DetectorFlatStep`
    - ``background_calc`` - `CalculateBackgroundImagerStep`
    - ``background_sub`` - `BackgroundSubtractionImagerStep`
    - ``assign_wcs`` - `AssignWCSStep`
    """

    # Define alias to steps
    step_defs = {
        "parse_subarrays": ParseSubarrayMapStep,
        "dark_sub": DarkSubtractionStep,
        "gain_corr": GainStep,
        "detflat": DetectorFlatStep,
        "background_calc": CalculateBackgroundImagerStep,
        "background_sub": BackgroundSubtractionImagerStep,
        "assign_wcs": AssignWCSStep,
    }

    class_alias = "stage2_imager"

    def process(self, input : dict) -> dict:

        import matplotlib
        matplotlib.use("QTAGG")
        import matplotlib.pyplot as plt
        import numpy as np
        #plt.imshow(np.log(input['SCI'][0].data), origin='lower')

        # Correct dark and flat
        sci_models = []
        for sci in input['SCI']:
            sci_model = self.parse_subarrays.run(sci)
            sci_model = self.dark_sub.run(sci_model)
            sci_model = self.gain_corr.run(sci_model)
            sci_model = self.detflat.run(sci_model)
            sci_models.append(sci_model)
        
        # Correct dark and flat for background files?
        # Calculate the background model
        if not self.background_calc.skip:
            if 'BKG' in input and len(input['BKG']) > 0:
                bkg_models = []
                for bkg in input['BKG']:
                    bkg_model = self.parse_subarrays.run(bkg)
                    bkg_model = self.dark_sub.run(bkg_model)
                    bkg_model = self.gain_corr.run(bkg_model)
                    bkg_model = self.detflat.run(bkg_model)
                    bkg_models.append(bkg_model)
                bkg_model = self.background_calc.run(bkg_models)
            else:
                bkg_model = self.background_calc.run(sci_models)
        else:
            self.background_calc.run(sci_models) # Skips background calc but logs in processing history table

        # Subtract the background from each science model
        if self.background_calc.bkg_result is not None and self.background_calc.bkg_result.get('scales', None):
            scales = self.background_calc.bkg_result['scales']
            for i in range(len(sci_models)):
                sci_models[i] = self.background_sub.run(sci_models[i], background=bkg_model, scale=scales[i])
        else:
            for i in range(len(sci_models)):
                sci_models[i] = self.background_sub.run(sci_models[i], background=bkg_model)

        # Assign the WCS to each science model
        for i in range(len(sci_models)):
            sci_models[i] = self.assign_wcs.run(sci_models[i])

        # Flux calibrate each science model
        # TODO: Implement flux calibration step
        #for i in range(len(sci_models)):
        #    sci_models[i] = self.flux_cal.run(sci_models[i])

        # Save the science models
        # for sci_model in sci_models:
        #     sci_model.meta.data_level = '2'
        #     if self.save_results:
        #         sci_model.save(output_dir=self.output_dir)

        # Return the list of science models
        return sci_models