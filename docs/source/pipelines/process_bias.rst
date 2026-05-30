=================================
Bias and kTC Calibration Pipeline
=================================

Overview
--------

The `ProcessBiasPipeline` uses a sequence of raw UTR (level 0) dark exposures to create a `BiasModel` calibration:

1.  **Data Quality Initialization** (dq_init):
    The `DQInitStep` populates the data quality (dq) mask for each input exposure according to pre-computed dq array.

2.  **Make Bias** (make_bias):
    The `MakeBiasStep` combines the inputs to create the bias calibration.


Input
+++++

- Raw UTR data: A list of `RampModel` (dark exposures).

Outputs
+++++++

- Bias calibration: `BiasModel`.
  Contains the measured bias frames and kTC noise extension.


Required Calibrations
+++++++++++++++++++++

- `DQModel` : Data quality calibration containing the pre-computed dq array. This is used to populate the input dq arrays for each exposure in `DQInitStep`.


API
---

.. autoclass:: liger_iris_pipeline.pipeline.process_bias_pipeline.ProcessBiasPipeline
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:
   :exclude-members: process