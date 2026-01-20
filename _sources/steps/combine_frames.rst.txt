Combine Frames
==============


Overview
--------

Combines a stack of frames.


**Class**: :py:class:`~liger_iris_pipeline.combine_frames.combine_frames_step.CombineFramesStep`


Algorithm
---------

A data cube is created from the input frames. The cube is then reduced according to the input argument ``method``. If ``method='sigma_clip'``, bad pixels are iteratively flagged before reduction. Currently only the sigma clipping method only implements cenfunc='median' and stdfunc='mad_std'.

The error is calculated in one of two ways:

1. ``error_calc='measure'`` : The error is calculated from the standard deviation of the values of the input frames.
2. ``error_calc='propagate'`` : The error is calculated from the propagation of the errors of the input frames:

    .. math::

        \sigma = \big( \sum_i \sigma_i^{-2} \big)^{-1/2}

where :math:`\sigma` is the error of the combined frame and :math:`\sigma_i` is the error of the input frames.


Arguments
---------
**input** : ``list[str |`` :py:class:`~liger_iris_pipeline.datamodels.LigerIRISDataModel` ``]``  
    The input data to combine.
**method** : ``str``  
    Method for combining the frames:
        - 'mean': Unweighted mean.
        - 'wmean': Weighted mean.
        - 'median': Unweighted median.
        - 'wmedian': Weighted median.
        - 'sigma_clip': Sigma clipping, see parameters below. Currently, only cenfunc='median' and stdfunc='mad_std' are supported.
**do_sigma_clip** : ``bool``  
    Whether to apply sigma clipping. Sigma clipping is performed using the biweight location and biweight midvariance (both unweighted), regardless of the `method` parameter.

**sigma_thresh_low** : ``float``  
    Number of standard deviations below the central value to flag as outliers.

**sigma_thresh_high** : ``float``  
    Number of standard deviations above the central value to flag as outliers.

**thresh_low** : ``float or None``  
    Absolute lower bound for outlier rejection. Values below this threshold will be excluded.

**thresh_high** : ``float or None``  
    Absolute upper bound for outlier rejection. Values above this threshold will be excluded.

**num_mask_low** : ``int or None``  
    Maximum number of low-end outliers to mask per batch.

**num_mask_high** : ``int or None``  
    Maximum number of high-end outliers to mask per batch.

**min_batch_size** : ``int``
    Minimum number of frames per batch required to apply sigma clipping.

**maxiters** : ``int``  
    Maximum number of iterations for the sigma clipping process.

**error_calc** : ``str``  
    Method for calculating the output error:
        - 'measure': Estimate from data dispersion.
        - 'propagate': Propagate errors from input values.


Subarrays
---------

TBD.

Calibration Files
-----------------

None