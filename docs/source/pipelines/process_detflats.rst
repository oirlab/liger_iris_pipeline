==================================
Detector Flat Calibration Pipeline
==================================

Overview
--------

The `ProcessDetFlatsPipeline` uses a sequence of raw UTR (level 0) detector flat exposures to create a `DetectorFlatModel` and `GainModel` calibration:

1.  **Data Quality Initialization** (dq_init):
    The `DQInitStep` populates the data quality mask for each input exposure.

2.  **Saturation Check** (sat_check):
    The `SaturationCheckStep` checks for any saturated pixels in each flat exposure and flags them in the data quality array. It is unlikely there are any saturated pixels in flat exposures, but it is included for completeness and consistency.

3.  **Bias Subtraction** (bias_sub):
    The `BiasSubtractionStep` subtracts the bias level from each flat exposure.

4. **Nonlinearity Correction** (nonlin_corr):
    The `NonlinearCorrectionStep` applies a nonlinearity correction to each flat exposure. Flat exposures are unlikely to exhibit significant nonlinearity, but this step is also included for completeness and consistency.

5. **Jump Detection** (jump_det):
    The `JumpDetectionStep` identifies any outliers (e.g. cosmic ray hits) in the flat exposures and flags them in the data quality array.

6. **Make Gain** (make_gain):
    The `MakeGainStep` calculates the gain from the flat exposures.

    In this step, both the gain and read noise are estimated using the maximum-likelihood framework provided by Tim Brandt (2025; PASP, 137, 125006, `arxiv link <https://arxiv.org/pdf/2512.09131>`_).

7. **Fit Ramps** (ramp_fit):
    The `RampFitStep` fits the ramps for each flat exposures to derive the count rates in DN/s.

8. **Dark Subtraction** (dark_sub):
    The `DarkSubtractionStep` subtracts the dark current from the count rates in DN/s for each flat exposure.

9. **Gain** (gain):
    The `GainStep` converts the count rates from DN/s to electrons/s.

10. **Coadd Frames** (coadd_frames):
    The `CoaddFramesStep` combines the 2D rate map frames in e-/s to create a single 2D frame.

11. **Make Detector Flat** (make_detflat):
    The `MakeDetectorFlatStep` converts the input data model to a `DetectorFlatModel` and additionally flags 'cold' pixels in the data quality array.

Input
+++++

- Raw UTR data: A list of `RampModel` (detector flat exposures).

Outputs
+++++++

A dictionary with the following entries:

- ``gain``: `GainModel`.
  Contains the measured gain.

- ``detflat``: `DetectorFlatModel`.
  Contains the measured detector flat.


API
---

.. autoclass:: liger_iris_pipeline.pipeline.process_detflats_pipeline.ProcessDetFlatsPipeline
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:
   :exclude-members: process