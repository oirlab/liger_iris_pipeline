Assign WCS
==========


Overview
--------

Associates a world coordinate system (WCS) object with each science exposure.


**Class**: :py:class:`~liger_iris_pipeline.assign_wcs.assign_wcs_step.AssignWCSStep`


Algorithm
---------

In general, there may be intermediate coordinate frames depending on the instrument. The WCS is saved in the ASDF extension of the FITS file. It can be accessed as an attribute of the meta object when the fits file is opened as a data model.

Currently the Liger IRIS DRS implements a very simple model that expects standard FITS WCS keywords in the header and uses ``astropy.modeling`` to build a transformation pipeline, wrap it into a generalized WCS ``gwcs.WCS`` object and store it as ``output_model.meta.wcs``, as it is expected by Stage 3 pipelines.

The forward direction of the transforms is from detector to world coordinates and the input positions are 0-based.

:py:class:`~liger_iris_pipeline.assign_wcs.assign_wcs_step.AssignWCSStep` expects to find the basic WCS keywords in the PRIMARY extension header. Distortion and spectral models are not implemented yet and will be stored in reference files in the `ASDF <http://asdf-standard.readthedocs.org/en/latest/>`__ format.


Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.imager.ImagerModel` | :py:class:`~liger_iris_pipeline.datamodels.ifu.IFUCubeModel`
    The input data to assign a WCS for.

Subarrays
---------

TBD.

Calibration Files
-----------------

WCS reference files are in the Advanced Scientific Data Format (ASDF). The best way to create the file is to programmatically create the model and then save it to a file. A tutorial on creating reference files in ASDF format is available at:

https://github.com/spacetelescope/jwreftools/blob/master/docs/notebooks/referece_files_asdf.ipynb

Transforms are 0-based. The forward direction is from detector to sky.