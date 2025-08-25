Normalize
=========


Overview
--------

Normalize a data model by dividing it by a normalization factor.


**Class**: :py:class:`~liger_iris_pipeline.normalize.normalize_step.NormalizeStep`


Algorithm
---------

The normalization factor is computed as either the mean, median, or mode of the data. This value is then divided into the data model's ``data``  and ``err`` attributes.

Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.imager.ImagerModel` | :py:class:`~liger_iris_pipeline.datamodels.ifu.IFUImageModel`
    The input data to remove the dark from.
**method** : ``str``
    The normalization method, either 'mean', 'median', or 'mode'. Default is 'mean'.

Subarrays
---------

TBD

Calibration Files
-----------------

None
