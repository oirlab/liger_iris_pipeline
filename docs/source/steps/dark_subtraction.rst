Dark Subtraction
================


Overview
--------

Subtracts the dark current from the input data.


**Class**: :py:class:`~liger_iris_pipeline.dark_subtraction.dark_step.DarkSubtractionStep`


Algorithm
---------

The appropriate master dark calibration is subtracted from the input data. The input's ``err`` attribute is updated by adding the dark's ``err`` attribute in quadarature. DQ flags are updated with bitwise or.

Any pixel values in the dark reference data that are set to ``NaN`` will have their values reset to zero before being subtracted from the science data, which will effectively skip the dark subtraction operation for those pixels.

Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.model_base.LigerIRISDataModel`
    The input data to remove the dark from.
**dark** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.dark.DarkModel`
    The name of the dark reference file or a dark model instance. If not provided, the dark is retrieved from the appropriate archive.

Subarrays
---------

The dark current is dependent on the detector read mode, therefore subarrays are corrected using the specified read mode.

Calibration Files
-----------------

- :doc:`dark <../datamodels/dark>`
