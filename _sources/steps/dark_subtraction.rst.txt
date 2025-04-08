========================
Dark Current Subtraction
========================

Description
-----------

The step :py:class:`~liger_iris_pipeline.dark_subtraction.dark_step.DarkSubtractionStep` subtracts a dark reference image from an input image.


Algorithm
---------

The SCI array from the dark reference file is subtracted from the SCI array of the science data set, and the dark DQ array is combined with the science DQ array using a bit-wise OR operation. The science ERR array is updated by adding the science and dark ERR arrays in quadrature.

Any pixel values in the dark reference data that are set to ``NaN`` will have their values reset to zero before being subtracted from the science data, which will effectively skip the dark subtraction operation for those pixels.


Subarrays
---------

The dark current is dependent on the detector read mode, therefore subarrays are corrected using the specified read mode.


Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.LigerIRISDataModel`
    The input science data to remove the dark from.
**dark** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.dark.DarkModel`
    The name of the dark reference file or a dark model instance. If not provided, the dark is retrieved from CRDS.


Reference Files
---------------

**dark** : Dark current reference file.
