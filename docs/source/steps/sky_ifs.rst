=============================
Sky Calc. & Subtraction (IFS)
=============================

Sky subtraction for the IFS can be handled in different ways depending on the available data products.


Sky Subtraction
+++++++++++++++

Description
-----------

The step :py:class:`~liger_iris_pipeline.sky_subtraction.sky_subtraction_ifs_step.SkySubtractionIFSStep` (under development) scales and subtracts a provided sky cube from an input image without any adjustments (or a simple scaling).


Algorithm
---------

The sky-subtraction algorithm will scale the sky frame to match each of the individual science frames, utilizing the Davies et al. 2007 methodology. Various OH lines arise from families of vibrational transitions. While sky lines can vary randomly throughout the night, these families fluctuate together. Using brighter sky lines, comparing the science and sky data cubes it is possible to determine the ratio between OH lines for each transition family. These ratios can be applied to the sky data cube in order to minimize the residuals in the subtracted cube. The scaling ratios are applied to the entire sky data cube, rather than to an extracted spectrum, such that any spatial or wavelength variations in the sky lines across the cube will still be accurately matched and cancelled out in the sky subtraction.


Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.IFSCubeModel` (or lists thereof)
    The input science data to calculate the sky from.

**sky** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.IFSCubeModel` (or lists thereof)
    The sky model to subtract from the input. If not provided, the sky will be queried with CRDS (TBD).


Calculate Sky Image
+++++++++++++++++++

Description
-----------

The step :py:class:`~liger_iris_pipeline.sky_subtraction.CreateSkyFrameIFSStep` (*under development*) creates a sky cube from a set of input cubes for IFS data. It also subtracts this sky frame from the user supplied IFS frames.


Algorithm
---------

Under development.

Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.ImagerModel` (or lists thereof)
    The input data to calculate the sky from.