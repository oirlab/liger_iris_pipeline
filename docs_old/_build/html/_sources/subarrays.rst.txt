*********************
Support for Subarrays
*********************

Support for subarrays is currently only implemented for the imager and it supports
datasets where only a custom subset of the 2D array is observed.

The keywords of :py:class:`ImagerModel` which defines the parameters of the subarray are::

    model.meta.subarray.name = "CUSTOM"
    model.meta.subarray.id = 1
    model.meta.subarray.xstart = xstart + 1
    model.meta.subarray.ystart = ystart + 1
    model.meta.subarray.xsize = xsize
    model.meta.subarray.ysize = ysize
    model.meta.subarray.detysiz = detysiz
    model.meta.subarray.detxsiz = detxsiz
    model.meta.subarray.fastaxis = 0
    model.meta.subarray.slowaxis = 1

Here the `xstart` and `ystart` keywords are converted from 0-based to 1-based indexing.
`xstart` and `ystart` are 1 by default. `subarray.id` is saved into the FITS keyword `SUBARRID` and should be 0 for full
frames, 1 for the first subarray and so on. The name of an entire frame is "FULL", whereas subarray names can be anything.

Subarrays and Reference Files
=============================

Flat frames, darks and background files either in CRDS or using local overrides
can either be saved as subarrays or can be saved as full frames.
In case they are saved as full frames, after being accessed they are sliced
according to the metadata in the input subarray.

Example Usage
=============

As usage examples, check the notebooks or the ``test_imager_stage2.py`` script in the
`unit tests folder in the repository <https://github.com/oirlab/liger_iris_pipeline/tree/master/liger_iris_pipeline/tests>`_

Related Steps
=============

.. toctree::
   :maxdepth: 2

   parse_subarray_map/index.rst
   merge_subarrays/index.rst
