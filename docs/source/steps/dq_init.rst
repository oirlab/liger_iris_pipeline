Data Quality Initialization
===========================


Overview
--------

Initializes the DQ array for the input dataset based on a static DQ map.

**Class**: :py:class:`~liger_iris_pipeline.dq_init.dq_init_step.DQInitStep`


Algorithm
---------

Flags from the appropriate static dq reference file in are copied into the ``PIXELDQ`` array of the input dataset, because it is assumed that flags in the dq reference file pertain to problem conditions that are group- and integration-independent.

#. Determine what dq reference file to use via the interface to the bestref utility in CRDS.

#. If the ``PIXELDQ`` or ``GROUPDQ`` arrays of the input dataset do not already exist, which is sometimes the case for raw input products, create these arrays in the input data model and initialize them to zero. The ``PIXELDQ`` array will be 2D, with the same number of rows and columns as the input science data. The ``GROUPDQ`` array will be 4D with the same dimensions (nints, ngroups, nrows, ncols) as the input science data array.

#. Check to see if the input science data is in subarray mode. If so, extract a matching subarray from the full-frame dq reference file.

#. Copy the DQ flags from the reference file dq to the science data ``PIXELDQ`` array using numpy's ``bitwise_or`` function.

..
  See an `example notebook on how to inizialize the bad pixel dq <https://gist.github.com/zonca/e15620ff5d26652bc201b180ec00cdce>`_ *(to be updated)


Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.ramp.RampModel`
    The input data to initialize the data quality mask for.
**dq** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.dark.DQModel`
    The name of the data quality reference file or a data quality model instance. If not provided, the data quality model is retrieved from the appropriate archive.

Subarrays
---------

TBD.

Calibration Files
-----------------

- :doc:`dark <../datamodels/data_quality>`

