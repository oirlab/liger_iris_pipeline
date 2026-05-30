=========================
Stage 2 Pipeline - Imager
=========================

Overview
--------

The `Stage2ImagerPipeline` is the main pipeline for processing raw 2D science frames (level 1) from the imager and converting them into level 2 fully calibrated frames.

1. **Parse Subarrays** (parse_subarrays) - *IRIS only*:
    The `ParseSubarrayMapStep` parses the subarray map array (``model.subarray_map``) to populate the subarray metadata (``meta.subarray``).

2.  **Dark Subtraction** (dark_sub):
    The `DarkSubtractionStep` subtracts the dark current from the input frames.

3.  **Gain Correction** (gain_corr):
    The `GainStep` applies a gain correction to the input frames to convert from DN/s to e-/s.

4.  **Detector Flat Field Correction** (detflat):
    The `DetectorFlatStep` applies a flat field correction to the input frames.

5.  **Background Calculation** (background_calc):
    The `CalculateBackgroundImagerStep` calculates the relative and spatially varying background level. If multiple inputs are provided, the calculated background is the average background up to a scale unique factor for each input.

6.  **Background Subtraction** (background_sub):
    The `BackgroundSubtractionImagerStep` subtracts the calculated background from the input frames.

7.  **Distortion Correction** (distortion):
    The `DistortionCorrectionStep` applies a distortion correction to the input frames.

8.  **Assign WCS** (assign_wcs):
    The `AssignWCSStep` assigns a WCS solution to the input frames.


Input
+++++

- Level 1 imager data: An `ImagerModel` or a list of them.

Outputs
+++++++

- A single 2D `ImagerModel` model or a list if given multiple inputs.


API
---

.. autoclass:: liger_iris_pipeline.pipeline.stage2_imager_pipeline.Stage2ImagerPipeline
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:
   :exclude-members: process