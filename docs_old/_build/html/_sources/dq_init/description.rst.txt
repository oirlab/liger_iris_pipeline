Description
============
The Data Quality (DQ) initialization step in the calibration pipeline
populates the DQ mask for the input dataset. Flags from the
appropriate static mask reference file in CRDS are copied into the
``PIXELDQ`` array of the input dataset, because it is assumed that flags in the
mask reference file pertain to problem conditions that are group- and
integration-independent.

We use the same flagging convention used for JWST, see
`their documentation <https://jwst-pipeline.readthedocs.io/en/latest/jwst/references_general/references_general.html#data-quality-flags>`_.

A bad pixel mask is a `datamodels.TMTMaskModel` object with a `dq` extension
with size `(4096x4096)` of time `uint32`.

It can be created with::

    from jwst.datamodels import TMTMaskModel
    f = TMTMaskModel()

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

    f.write(Path.home() / "crds_cache/references/tmt/iris/tmt_iris_mask_0001.fits")

Which flag is picked up by the pipeline is determined by the `tmt_iris_mask_0001.rmap` file,
see `the current file content on Github <https://github.com/oirlab/tmt-crds-cache/blob/master/mappings/tmt/tmt_iris_mask_0001.rmap>`_.

The actual process consists of the following steps:

 - Determine what MASK reference file to use via the interface to the bestref
   utility in CRDS.

 - If the ``PIXELDQ`` or ``GROUPDQ`` arrays of the input dataset do not already exist,
   which is sometimes the case for raw input products, create these arrays in
   the input data model and initialize them to zero. The ``PIXELDQ`` array will be
   2D, with the same number of rows and columns as the input science data.
   The ``GROUPDQ`` array will be 4D with the same dimensions (nints, ngroups,
   nrows, ncols) as the input science data array.

 - Check to see if the input science data is in subarray mode. If so, extract a
   matching subarray from the full-frame MASK reference file.

 - Copy the DQ flags from the reference file mask to the science data ``PIXELDQ``
   array using numpy's ``bitwise_or`` function.

See an `example notebook on how to inizialize the bad pixel mask <https://gist.github.com/zonca/e15620ff5d26652bc201b180ec00cdce>`_.
