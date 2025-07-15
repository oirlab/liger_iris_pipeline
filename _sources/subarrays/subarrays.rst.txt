=========
Subarrays
=========

Subarrays are exposures captured using a custom rectangular window within the detector array. Subarrays are only supported for the Imager.

The meta keywords of :py:class:`~liger_iris_pipeline.datamodels.imager.ImagerModel` which defines the parameters of the subarray are stored in ``model.meta.subarray_map``:


* ``name (str)``: The name of the subarray. This can be "FULL" for full frame or any other name for a subarray.
* ``id (int)``: The id of the subarray. This is 0 for full frame and 1 for the first subarray, etc.
* ``xstart (int)``: The starting x-coordinate of the subarray in 1-based indexing.
* ``ystart (int)``: The starting y-coordinate of the subarray in 1-based indexing.
* ``xsize (int)``: The width of the subarray.
* ``ysize (int)``: The height of the subarray.
* ``detysiz (int)``: The height of the detector (full frame).
* ``detxsiz (int)``: The width of the detector (full frame).
* ``fastaxis (int)``: The fast axis of the subarray {0,1}.
* ``slowaxis (int)``: The slow axis of the subarray {0,1}.


Subarrays and Reference Files
-----------------------------

The following reference files support subarrays due to the unique read mode used for that subarray:

* **dark**: Dark current reference file.
* **linearity**: Linearity correction reference file.
* **saturation**: Saturation reference file.
* **bias**: Superbias reference file.
* **gain**: Gain reference file.
* **readnoise**: Read noise reference file.
* **ipc**: Interpixel capacitance reference file.
* **flat**: Flat field reference file.


Example
-------

See the test scripts in the DRS tests directory:

- `test_imager_stage2.py <https://github.com/oirlab/liger_iris_pipeline/blob/master/liger_iris_pipeline/tests/test_imager_stage2.py>`_
- `test_parse_subarray_map.py <https://github.com/oirlab/liger_iris_pipeline/blob/master/liger_iris_pipeline/tests/test_parse_subarray_map.py>`_
- `test_merge_subarrays.py <https://github.com/oirlab/liger_iris_pipeline/blob/master/liger_iris_pipeline/tests/test_merge_subarrays.py>`_
- `test_create_subarray_dataset.py <https://github.com/oirlab/liger_iris_pipeline/blob/master/liger_iris_pipeline/tests/test_create_subarray_dataset.py>`_
- `test_dark_subarray.py <https://github.com/oirlab/liger_iris_pipeline/blob/master/liger_iris_pipeline/tests/test_dark_subarray.py>`_


Subarray-specific Steps
-----------------------

Many steps use specific processing for subarrays.

* :py:class:`~liger_iris_pipeline.merge_subarrays.merge_subarrays.MergeSubarraysStep`
* :py:class:`~liger_iris_pipeline.parse_subarray_map.parse_subarray_map_step.ParseSubarrayMapStep`