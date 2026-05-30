================
Stage 1 Pipeline
================

Overview
--------

The `Stage1Pipeline` processes raw UTR cube data (level 0) into 2D frames (level 1) and can be applied to any UTR data product.

1.  **Data Quality Initialization** (dq_init):
    The `DQInitStep` populates the data quality mask for each input exposure.

2.  **Saturation Check** (sat_check):
    The `SaturationCheckStep` checks for any saturated pixels in each input exposure and flags them in the data quality array.

3.  **Bias Subtraction** (bias_sub):
    The `BiasSubtractionStep` subtracts the bias level from each input exposure.

4. **Nonlinearity Correction** (nonlin_corr):
    The `NonlinearCorrectionStep` applies a nonlinearity correction to each input exposure.

5. **Jump Detection** (jump_det):
    The `JumpDetectionStep` identifies any outliers (e.g. cosmic ray hits) in the input exposures and flags them in the data quality array.
    
6. **Fit Ramps** (ramp_fit):
    The `RampFitStep` fits the ramps for each input exposures to derive the count rates in DN/s.


Input
+++++

- Raw UTR data: A `RampModel` or a list of them.

Outputs
+++++++

`Stage1Pipeline` returns a single 2D image model or a list if given multiple inputs.

- For **Imager** data (``meta.instrument.mode == "IMG"`` ), the output type is a `ImagerModel`.

- For **IFS** data (``meta.instrument.mode == "IFS"`` ), the output type is `IFSImageModel`.


API
---

.. autoclass:: liger_iris_pipeline.pipeline.stage1_pipeline.Stage1Pipeline
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:
   :exclude-members: process