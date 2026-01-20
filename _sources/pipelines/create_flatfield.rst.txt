Create Flatfield
================

Overview
--------

Creates a flat field calibration file from a set of uncalibrated 2D rate-maps.

**Class**: :py:class:`~liger_iris_pipeline.pipeline.create_flatfield.CreateFlatfield` 


Steps
-----

1. :doc:`Dark Subtraction <../steps/dark_subtraction>`
    The appropriate dark reference file is first subtracted from each uncalibrated 2D rate-map using the specified dark subtraction algorithm.
2. :doc:`Combine Frames <../steps/combine_frames>`
    The frames are first combined into a single 2D rate-map using the specified reduction algorithm.
3. :doc:`Normalize Image <../steps/normalize>`
    The rate-map is then normalized to 1 using the specified normalization algorithm.


Arguments
---------

None.