=========
Subarrays
=========

Subarrays are exposures captured using a custom rectangular window within the detector array. Subarrays are only supported for the IRIS Imager.

The meta keywords ``model.meta.subarray`` for `ImagerModel` define the subarray parameters used for that exposure:

* ``name (str)``: The name of the subarray. This can be "FULL" for full frame or any other name for a subarray.
* ``id (int)``: The id of the subarray. This is 0 for full frame and 1 for the first subarray, etc.
* ``xstart (int)``: The starting x-coordinate of the subarray in 1-based indexing.
* ``ystart (int)``: The starting y-coordinate of the subarray in 1-based indexing.
* ``xsize (int)``: The width of the subarray.
* ``ysize (int)``: The height of the subarray.
* ``detysiz (int)``: The height of the detector (full frame).
* ``detxsiz (int)``: The width of the detector (full frame).
* ``fastaxis (int)``: The fast axis of the subarray (0 or 1).
* ``slowaxis (int)``: The slow axis of the subarray (0 or 1).

The extension SUBARRAY_MAP (``model.subarray_map``) is a 2D array (Uint8) of subarray ids.

The data quality array (``model.dq``) uses a special bit called SUBARRAY to denote a pixel is part of a subarray.


Subarrays Support
-----------------

Any steps that can process imager data can also process subarray data. The subarray metadata is preserved throughout the pipeline processing. Formally defining support will be done in future releases.

Examples
--------

See the test scripts in the DRS tests directory:

- `test_imager_stage2.py <https://github.com/oirlab/liger_iris_pipeline/blob/master/liger_iris_pipeline/tests/test_imager_stage2.py>`_
- `test_parse_subarray_map.py <https://github.com/oirlab/liger_iris_pipeline/blob/master/liger_iris_pipeline/tests/test_parse_subarray_map.py>`_
- `test_merge_subarrays.py <https://github.com/oirlab/liger_iris_pipeline/blob/master/liger_iris_pipeline/tests/test_merge_subarrays.py>`_
- `test_create_subarray_dataset.py <https://github.com/oirlab/liger_iris_pipeline/blob/master/liger_iris_pipeline/tests/test_create_subarray_dataset.py>`_
- `test_dark_subarray.py <https://github.com/oirlab/liger_iris_pipeline/blob/master/liger_iris_pipeline/tests/test_dark_subarray.py>`_


Subarray-specific Steps
-----------------------

Several steps are specifically designed to parse or transform the subarray metadata:

- `ParseSubarrayMapStep`
    Parse a single DataModel's ``model.subarray_map`` extension (2D array) and populate the attribute ``model.meta.subarray``, and object describing a single subarray.

- `MergeSubarraysStep`
    Merge multiple subarrays into one DataModel.