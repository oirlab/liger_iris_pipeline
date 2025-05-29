=====================
Flat Field Correction
=====================


Description
-----------

The flat field correction step :py:class:`~liger_iris_pipeline.flat_field.flat_field_step.FlatFieldStep` divides an input image by a flat field reference image.


Algorithm
---------

The SCI array from the flat-field reference file is divided into both the SCI and ERR arrays of the science data set, and the flat-field DQ array is combined with the science DQ array using a bit-wise OR operation.

For pixels whose DQ is NO_FLAT_FIELD in the reference file, the flat value is reset to 1.0. Similarly, for pixels whose flat value is NaN, the flat value is reset to 1.0 and DQ value in the output science data is set to NO_FLAT_FIELD. In both cases, the effect is that no flat-field is applied.

If any part of the input data model gets flat-fielded, the status keyword S_FLAT will be set to COMPLETE in the output science data.

Subarrays
---------

If the reference data arrays are the same size as the science data, they will be applied directly. If there is a mismatch, the routine will extract the matching subarray from the reference file data arrays and apply them to the science data. Hence full-frame reference files can be used for both full-frame and subarray science exposures, or subarray-dependent reference files can be used if appropriate.


Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.LigerIRISDataModel`
    The input file or data model to process.
**flat** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.flat.FlatModel` | ``None``
    The name of the flat field reference file or a flat field model. If not provided, the flat is retrieved with CRDS.


Reference Files
---------------

**flat**
