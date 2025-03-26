===============
Merge Subarrays
===============


Description
-----------

The step :py:class:`~liger_iris_pipeline.merge_subarrays.merge_subarrays.MergeSubarraysStep` merges a set of individual subarrays into an effective full frame image. This is a level 3 tool; it assumes the inputs have been already processed by the appropriate Stage 2 Pipeline.

As an example, see `test_merge_subarrays.py <https://github.com/oirlab/liger_iris_pipeline/blob/master/liger_iris_pipeline/tests/dev_test_merge_subarrays.py>`_.


Algorithm
---------

Currently the algorithm is trivial, it only puts back the relevant slices of the ``data``, ``dq`` and ``err`` extensions in the correct location without any modifications.


Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.imager.ImagerModel`
    The input file to process.