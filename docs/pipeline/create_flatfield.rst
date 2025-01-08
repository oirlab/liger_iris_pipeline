.. _preprocess_flatfield:

preprocess_flatfield: Preprocess Flat fields
============================================

:Config: preprocess_flatfield.cfg
:Class: `~liger_iris_pipeline.pipeline.ProcessFlatfieldL2`

Stage 2 imaging processing applies additional instrumental corrections and
calibrations that result in a fully calibrated individual exposure. 

The list of steps applied by the ``ProcessImagerL2Pipeline`` pipeline is shown in the table
below, currently only the ``background``, ``dark_current`` and ``flat_field`` have
been imported into ``liger_iris_pipeline`` and customized for IRIS.
The other steps still call classes from ``jwst`` and have not been tested, they
are still in the class to simplify the future porting process.

+-----------------------------------------+
| image2                                  |
+=========================================+
| :ref:`dark_current <dark_current_step>` |
+-----------------------------------------+
| :ref:`normalize <normalize_step>`       |
+-----------------------------------------+

Arguments
---------

None

Inputs
------

2D data
^^^^^^^

:Data model: `~liger_iris_pipeline.datamodels.IRISImageModel`

The input to ``ProcessFlatfieldL2`` is
a raw exposure to be normalized in order to be used as a Flat field.

Outputs
-------

2D normalized flat field
^^^^^^^^^^^^^^^^^^^^^^^^

:Data model: `~liger_iris_pipeline.datamodels.IRISImageModel`
:File suffix: _flat

Normalized flat ready to be used by the :ref:`flatfield_step`,
or the :ref:`image2` pipeline or ready
to be ingested into the CRDS for later usage.
