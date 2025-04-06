Create Dark
===========

Description
-----------

The pipeline :py:class:`~liger_iris_pipeline.pipeline.create_dark.CreateDark` creates a dark reference file from a set of uncalibrated 2D rate-maps.


Steps
-----

1. CombineFramesStep.
    The frames are first combined into a single 2D rate-map using the :py:class:`~liger_iris_pipeline.pipeline.combine_frames.CombineFramesStep` step.

The resulting rate-map is then used to initialize a dark reference file.