================
Bias Subtraction
================

Description
-----------

The step :py:class:`~liger_iris_pipeline.bias_subtraction.bias_step.BiasSubtractionStep` subtracts the bias level from the input data. The bias correction can be performed on L0 (ramp) or L1 (rate map) data models.


Algorithm
---------

The bias is subtracted from the the input data. The errors are added in quadrature. DQ flags are combined using a bitwise OR operation.

Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.ramp.RampModel`
    The input file or ramp model to process.
**bias** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.bias.BiasModel` | ``None`` (FIX LINK)
    The name of the bias reference file or a bias model instance. If not provided, the bias is retrieved from CRDS.


Subarrays
---------

The bias level depends on the detector read mode, therefore subarrays are corrected using the specified read mode.


Reference Files
---------------

:py:class:`~liger_iris_pipeline.datamodels.bias.BiasModel`