Merge Subarrays
===============


Overview
--------

Merges a set of individual subarrays into an effective full frame image. This is a level 3 tool; it assumes the inputs have been already processed by the appropriate Stage 2 Pipeline.


**Class**: :py:class:`~liger_iris_pipeline.merge_subarrays.merge_subarrays_step.MergeSubarraysStep`


Algorithm
---------

Currently the algorithm is trivial, it only puts back the relevant slices of the ``data``, ``dq`` and ``err`` extensions in the correct location without any modifications.

Arguments
---------

**input** : ``dict``
    The input dictionary (TBD).

Subarrays
---------

TBD

Calibration Files
-----------------

- :doc:`dark <../datamodels/dark>`