Create Flatfield
================

Description
-----------

The pipeline :py:class:`~liger_iris_pipeline.pipeline.create_flatfield.CreateFlatfield` creates a flat reference file from a set of uncalibrated 2D rate-maps.


Steps
-----

1. DarkSubtractionStep
    The dark reference file is first subtracted from each uncalibrated 2D rate-map using the :py:class:`~liger_iris_pipeline.pipeline.dark_subtraction.DarkSubtractionStep` step.
2. CombineFramesStep.
    The frames are first combined into a single 2D rate-map using the :py:class:`~liger_iris_pipeline.pipeline.combine_frames.CombineFramesStep` step.
3. NormalizeStep.
    The rate-map is then normalized to 1 using the :py:class:`~liger_iris_pipeline.pipeline.normalize.NormalizeStep` step.

The resulting rate-map is then used to initialize a flatfield reference file.