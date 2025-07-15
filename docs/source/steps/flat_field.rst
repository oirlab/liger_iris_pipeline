Flat Field Correction
=====================


Overview
--------

Corrects the pixel-to-pixel variations in the detector response by applying a flat field correction to the input data.


**Class**: :py:class:`~liger_iris_pipeline.flat_field.flat_field_step.FlatFieldStep`


Algorithm
---------

The appropriate master flat calibration is divided into the input data. The input's ``err`` attribute is updated by adding the dark's ``err`` attribute in quadarature under a linear assumption. DQ flags are updated with bitwise or.

Any pixel values in the flat field reference data that are set to ``NaN`` will have their values reset to one before being divided into the science data, which will effectively skip the flat field operation for those pixels.

Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.imager.ImagerModel` | :py:class:`~liger_iris_pipeline.datamodels.ifu.IFUImageModel`
    The input data to remove the dark from.
**flat** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.flat.FlatModel` | ``None``
    The name of the flat field reference file or a flat field model instance. If not provided, the flat field is retrieved from the appropriate archive.

Subarrays
---------

The flat field is dependent on the detector read mode, therefore subarrays are corrected using the specified read mode.

Calibration Files
-----------------

- :doc:`dark <../datamodels/flat>`