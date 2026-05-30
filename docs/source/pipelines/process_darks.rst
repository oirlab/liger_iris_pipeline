=======================================
Dark and Readnoise Calibration Pipeline
=======================================

Overview
--------

The `ProcessDarksPipeline` uses a sequence of raw UTR (level 0) dark exposures to create a `DarkModel` and `ReadNoiseModel` calibration:

1.  **Data Quality Initialization** (dq_init):
    The `DQInitStep` populates the data quality mask for each input exposure.

2.  **Make Bias** (make_bias):
    The `MakeBiasStep` combines the inputs to create the bias calibration.

3.  **Saturation Check** (sat_check):
    The `SaturationCheckStep` checks for any saturated pixels in each dark exposure and flags them in the data quality array. It is unlikely there are any saturated pixels in dark exposures, but it is included for completeness and consistency.

4.  **Bias Subtraction** (bias_sub):
    The `BiasSubtractionStep` subtracts the bias level from each dark exposure.

5. **Nonlinearity Correction** (nonlin_corr):
    The `NonlinearCorrectionStep` applies a nonlinearity correction to each dark exposure. Dark exposures are unlikely to exhibit significant nonlinearity, but this step is also included for completeness and consistency.

6. **Jump Detection** (jump_det):
    The `JumpDetectionStep` identifies any outliers (e.g. cosmic ray hits) in the dark exposures and flags them in the data quality array.

7. **Make Read Noise** (make_rn):
    The `MakeReadNoiseStep` calculates the read noise from the dark exposures.

    The read noise is calculated using the maximum-likelihood framework provided by Tim Brandt (2025; PASP, 137, 125006, `arxiv link <https://arxiv.org/pdf/2512.09131>`_). In this step, the gain is held fixed and only the read noise is estimated.

8. **Fit Ramps** (ramp_fit):
    The `RampFitStep` fits the ramps for each dark exposures to derive the count rates in DN/s.

9. **Coadd Frames** (coadd_frames):
    The `CoaddFramesStep` combines the 2D count rate frames from the individual dark exposures to create a single 2D frame.

10. **Make Dark** (make_dark):
    The `MakeDarkStep` converts the input data model to a `DarkModel` and flags pixels where the dark current is higher than a specified threshold.

Input
+++++

- Raw UTR data: A list of `RampModel` (dark exposures).

Outputs
+++++++

A dictionary with the following entries:

- ``dark``: `DarkModel`.
  Contains the measured dark current.

- ``read_noise``: `ReadNoiseModel`.
  Contains the measured read noise.


API
---

.. autoclass:: liger_iris_pipeline.pipeline.process_darks_pipeline.ProcessDarksPipeline
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:
   :exclude-members: process