==============
Combine Frames
==============

Description
-----------

The step :py:class:`~liger_iris_pipeline.combine_frames.combine_frames_step.CombineFramesStep` combines a stack of frames.


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
        - 'wmedian' : Weighted median.
        - 'sigma_clip' : Sigma clipping, see arguments sigma, cenfunc, stdfunc, maxiters. Currently, only cenfunc='median' and stdfunc='mad_std' are supported.
