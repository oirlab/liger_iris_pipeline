===========================
Data Quality Initialization
===========================


Description
-----------
The step :py:class:`~liger_iris_pipeline.dq_init.dq_init_step.DQInitStep` populates the DQ mask for the input dataset. Flags from the appropriate static dq reference file in CRDS are copied into the ``PIXELDQ`` array of the input dataset, because it is assumed that flags in the dq reference file pertain to problem conditions that are group- and integration-independent.

We use the same flagging convention used for JWST, `documentated here <https://jwst-pipeline.readthedocs.io/en/latest/jwst/references_general/references_general.html#data-quality-flags>`_.

A data quality model is a :py:class:`~liger_iris_pipeline.datamodels.dq.DQModel` object with a 2D ``DQ`` ``ImageHDU`` extension with datatype `uint32`. The size depends on the detector.


It can be created with::

    from liger_iris_pipeline.datamodels import DQModel
    import numpy as np
    import from pathlib import Path
    
    model = DQModel()

First we need to setup metadata::

    f.meta.name = "IRIS"
    f.meta.detector = "IRIS1"

Then we can create the 2D array and set some flag value::

    f.dq = np.zeros((4096,4096))
    f.dq[np.random.randint(0, 4096, size=(10,2))] = 1024 # dead pixel
    f.dq[np.random.randint(0, 4096, size=(10,2))] = 2048 # hot pixel

check the content of the flag::

    np.histogram(f.dq, bins=3)
    (array([16777196,       10,       10]),
     array([   0.        ,  682.66666667, 1365.33333333, 2048.        ]))

And finally write to the `CRDS` cache::

    f.write(Path.home() / "crds_cache/references/ligeriri/iris/iris_dq_0001.fits")


Which flag is picked up by the pipeline is determined by the file `ligeriri_iris_dq_0001.rmap <https://github.com/oirlab/liger-iris-crds-cache/blob/master/mappings/ligeriri/ligeriri_iris_dq_0001.rmap>`_.

The actual process consists of the following steps:

#. Determine what dq reference file to use via the interface to the bestref utility in CRDS.

#. If the ``PIXELDQ`` or ``GROUPDQ`` arrays of the input dataset do not already exist, which is sometimes the case for raw input products, create these arrays in the input data model and initialize them to zero. The ``PIXELDQ`` array will be 2D, with the same number of rows and columns as the input science data. The ``GROUPDQ`` array will be 4D with the same dimensions (nints, ngroups, nrows, ncols) as the input science data array.

#. Check to see if the input science data is in subarray mode. If so, extract a matching subarray from the full-frame dq reference file.

#. Copy the DQ flags from the reference file dq to the science data ``PIXELDQ`` array using numpy's ``bitwise_or`` function.

..
  See an `example notebook on how to inizialize the bad pixel dq <https://gist.github.com/zonca/e15620ff5d26652bc201b180ec00cdce>`_ *(to be updated).
