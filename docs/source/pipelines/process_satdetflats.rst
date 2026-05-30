============================================
Saturated Detector Flat Calibration Pipeline
============================================

Overview
--------

The `ProcessSatDetFlatsPipeline` uses a sequence of raw UTR (level 0) detector flat exposures to create a `SaturationModel` and `NonlinearCorrectionModel` calibration:

1.  **Data Quality Initialization** (dq_init):
    The `DQInitStep` populates the data quality mask for each input exposure.

2. **Make Saturation Map** (make_sat):
    The `MakeSaturationStep` creates a saturation map describing the per-pixel saturation threshold.

3.  **Saturation Check** (sat_check):
    The `SaturationCheckStep` checks for any saturated pixels in each flat exposure and flags them in the data quality array. It is unlikely there are any saturated pixels in flat exposures, but it is included for completeness and consistency.

4.  **Bias Subtraction** (bias_sub):
    The `BiasSubtractionStep` subtracts the bias level from each flat exposure.

5. **Make Nonlinearity Map** (make_nonlin):
    The `MakeNonLinStep` creates a nonlinearity map describing the per-pixel nonlinearity correction coefficients using the framework described in Brandt (2025) - `ADS link <https://ui.adsabs.harvard.edu/abs/2025PASP..137l5005B/abstract>`_.


Input
+++++

- Raw UTR data: A list of `RampModel` (detector flat exposures).

Outputs
+++++++

A dictionary with the following entries:

- ``nonlin``: `NonlinearCorrectionModel`.
  Contains the measured nonlinearity correction coefficients.

- ``saturation``: `SaturationModel`.
  Contains the measured saturation threshold for each pixel.


API
---

.. autoclass:: liger_iris_pipeline.pipeline.process_satdetflats_pipeline.ProcessSatDetFlatsPipeline
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:
   :exclude-members: process