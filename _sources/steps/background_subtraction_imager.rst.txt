Background Subtraction (Imager)
===============================


Overview
--------

Calculates and subtracts the background sky background from imager data. This is done in 2 separate steps and may be combined into one step if appropriate.

**Classes:**
- :py:class:`~liger_iris_pipeline.background.calc_background_imager_step.CalculateBackgroundImagerStep`
- :py:class:`~liger_iris_pipeline.background.subtract_background_imager_step.SubtractBackgroundImagerStep`


Algorithm
---------

The background is computed from either the input science data or a dedicated background data. If several exposures are provided, the background is computed as an average of the scaled input data.

The appropriate master background calibration is subtracted from the input data. The input's ``err`` attribute is updated by adding the background's ``err`` attribute in quadrature. DQ flags are updated with bitwise or.

Arguments
---------

**Calculate Background**:

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.imager.ImagerModel` | ``list``
    The input data to calculate the background from. This can be a single exposure or a list of exposures.
**box_size** : ``int``
    The box size along each axis. If box_size is a scalar then a square box of size box_size will be used. If box_size has two elements, they must be in (ny, nx) order. For best results, the box shape should be chosen such that the data are covered by an integer number of boxes in both dimensions. When this is not the case, see the edge_method keyword for more options.
**filter_size** : ``int``
    The window size of the 2D median filter to apply to the low-resolution background map. If filter_size is a scalar then a square box of size filter_size will be used. If filter_size has two elements, they must be in (ny, nx) order. filter_size must be odd along both axes. A filter size of 1 (or (1, 1)) means no filtering.
**sigma_low** : ``float``
    The lower sigma threshold for sigma clipping for the background calculation.
**sigma_high** : ``float``
    The upper sigma threshold for sigma clipping for the background calculation.
**maxiters** : ``int``
    The maximum number of iterations for sigma clipping to perform when calculating the background.

**Subtract Background**:

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.imager.ImagerModel`
    The input data to remove the dark from.
**background** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.imager.ImagerModel`
    The name of the background file or a imager model instance.


Calibration Files
^^^^^^^^^^^^^^^^^

TBD
