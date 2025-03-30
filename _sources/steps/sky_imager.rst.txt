================================
Sky Calc. & Subtraction (Imager)
================================

Sky subtraction for the imager can be handled in different ways depending on the available data products.


Static Sky Subtraction
++++++++++++++++++++++

Description
-----------

The step :py:class:`~liger_iris_pipeline.sky_subtraction.sky_subtraction_imager_step.SkySubtractionImagerStep` subtracts a provided sky image from an input image without any adjustments (or a simple scaling).


Algorithm
---------

Determine scaling (maybe)

Simple background subtraction and error propagation.

Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.ImagerModel` (or lists thereof)
    The input science data to calculate the sky from.

**sky** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.ImagerModel` (or lists thereof)
    The sky model to subtract from the input. If not provided, the sky will be queried with CRDS (TBD).

**scale** : ``bool``
    The scaling factor to apply to the sky image before subtraction. Defaults to ``False``.


Calculate Sky Image
+++++++++++++++++++

Description
-----------

The step :py:class:`~liger_iris_pipeline.sky_subtraction.CreateSkyFrameImagerStep` (*under development*) creates a sky image from a set of input images for imager data. It also subtracts this sky frame from the user input images.


Algorithm
---------

The algorithm is based on the following steps from Clement et al. 2012 (find link):

1. Subtract median from each image (detector)
2. Account for gain and sky, apply 5 sigma rejection (i.e. MAD)
3. Keep track of the values subtracted
4. For each individual median subtracted image:
5. Run SExtractor to detect all objects in frame and generate an object mask.
6. Save “-object” check image
7. Compute the median of each pixel using the mask computed previously but not including the pixel from the image you are working on
8. Add background value from (3) to the median computed in (1), this will be the new sky background
9. Subtract the new background from original image


Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.ImagerModel` (or lists thereof)
    The input science data to calculate the sky from.

**sigma** : ``float``
    The number of standard deviations to use for the clipping limit. Defaults to 4.

**maxiters** : ``int`` | ``None``
    The number of clipping iterations to perform, or ``None`` to clip until convergence is achieved. Defaults to ``None``.