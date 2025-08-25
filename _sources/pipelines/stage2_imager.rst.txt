Stage 2 Imager
==============

Overview
--------

The pipeline  converts the raw 2D rate-maps from stage 1 into fully calibrated individual exposures.

**Class**: :py:class:`~liger_iris_pipeline.pipeline.imager_stage2.ImagerStage2Pipeline`

Steps
-----

1. :doc:`Combine Frames <../steps/parse_subarrays>`
2. :doc:`Dark Subtraction <../steps/dark_subtraction>`
3. :doc:`Flat Field <../steps/flat_field>`
4. :doc:`Background Subtraction <../steps/background_subtraction_imager>`
5. :doc:`Assign WCS <../steps/assign_wcs>`
6. ``Photom`` (*Under development*)
7. ``Resample`` (*Under development*)

Arguments
---------

Pipeline specific arguments.


