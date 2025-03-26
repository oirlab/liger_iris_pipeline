.. _merge_subarrays:

===============
Merge subarrays
===============

Description
===========

Merge a full frame with concurrent subarrays.
This is a level 3 tool, it assumes the inputs have been already reduced by a level 2 tool (the image2 pipeline in this case).

It takes a pointer to the full frame and the subarrays and combines them back into a single reduced file.

Input
=====

The input is a Level 3 association file, it includes paths to the FITS files for the
full frame and all the subarrays.

As an example, checkout the `test_merge_subarrays.ipynb` notebook in the `tests/` folder.

Merging algorithm
=================

Currently the algorithm is trivial, it only puts back the relevant slices of the
`data`, `dq` and `err` extensions in the correct location without any modification.

Output
======

A single reduced full-frame.


.. automodapi:: liger_iris_pipeline.merge_subarrays
