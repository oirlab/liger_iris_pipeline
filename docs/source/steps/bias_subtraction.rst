Bias Subtraction
================


Overview
--------

Subtracts the bias from the input data.


**Class**: TBD


Algorithm
---------

The appropriate master bias calibration is subtracted from the input data. The input's ``err`` attribute is updated by adding the dark's ``err`` attribute in quadarature. DQ flags are updated with bitwise or.

Any pixel values in the bias reference data that are set to ``NaN`` will have their values reset to zero before being subtracted from the science data, which will effectively skip the bias subtraction operation for those pixels.

Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.ramp.RampModel`
    The input data to remove the bias from.
**bias** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.bias.BiasModel`
    The name of the bias reference file or a dark model instance. If not provided, the bias is retrieved from the appropriate archive.

Subarrays
---------

The bias is dependent on the detector read mode, therefore subarrays are corrected using the specified read mode.

Calibration Files
-----------------

- :doc:`dark <../datamodels/bias>`
