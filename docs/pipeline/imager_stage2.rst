.. _image2:

image2: Stage 2 Imaging Processing
==================================

:Config: image2.cfg
:Class: `~liger_iris_pipeline.pipeline.ImagerStage2Pipeline`

Stage 2 imaging processing applies additional instrumental corrections and
calibrations that result in a fully calibrated individual exposure. 

The list of steps applied by the ``ProcessImagerL2Pipeline`` pipeline is shown in the table
below, currently only the ``background``, ``dark_current`` and ``flat_field`` have
been imported into ``liger_iris_pipeline`` and customized for IRIS.
The other steps still call classes from ``jwst`` and have not been tested, they
are still in the class to simplify the future porting process.

+----------------------------------------------------------------------+
| image2                                                               |
+======================================================================+
| :ref:`background <background_step>`                                  |
+----------------------------------------------------------------------+
| :ref:`parse subarray map <parse_subarray_map_step>`                  |
+----------------------------------------------------------------------+
| :ref:`assign_wcs <assign_wcs_step>`                                  |
+----------------------------------------------------------------------+
| :ref:`dark_current <dark_current_step>`                              |
+----------------------------------------------------------------------+
| :ref:`flat_field <flatfield_step>`                                   |
+----------------------------------------------------------------------+
| :ref:`photom <photom_step>`                                          |
+----------------------------------------------------------------------+
| :ref:`resample <resample_step>`                                      |
+----------------------------------------------------------------------+


Arguments
---------

The ``image2`` pipeline has one optional argument::

  --save_bsub  boolean  default=False

If set to ``True``, the results of
the background subtraction step will be saved to an intermediate file,
using a product type of "_bsub" or "_bsubints", depending on whether the
data are 2D (averaged over integrations) or 3D (per-integration results).

Inputs
------

2D or 3D countrate data
^^^^^^^^^^^^^^^^^^^^^^^

:Data model: `~liger_iris_pipeline.datamodels.IRISImageModel`
:File suffix: _rate or _rateints

The input to ``ProcessImagerL2Pipeline`` is
a countrate exposure, in the form of either "_rate" or "_rateints"
data. A single input file can be processed or an ASN file listing
multiple inputs can be used, in which case the processing steps will be
applied to each input exposure, one at a time. If "_rateints" products are
used as input, each step applies its algorithm to each
integration in the exposure, where appropriate.

Outputs
-------

2D or 3D background-subtracted data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:Data model: `~liger_iris_pipeline.datamodels.IRISImageModel`
:File suffix: _bsub or _bsubints

This is an intermediate product that is only created if "--save_bsub" is set
to ``True`` and will contain the data as output from the
:ref:`background <background_step>` step.
If the input is a "_rate" product, this will be a "_bsub" product, while
"_rateints" inputs will be saved as "_bsubints."

2D or 3D calibrated data
^^^^^^^^^^^^^^^^^^^^^^^^

:Data model: `~liger_iris_pipeline.datamodels.IRISImageModel`
:File suffix: _cal or _calints

The output is a fully calibrated, but unrectified, exposure, using
the product type suffix "_cal" or "_calints", depending on the type of
input, e.g. "jw80600012001_02101_00003_mirimage_cal.fits".
