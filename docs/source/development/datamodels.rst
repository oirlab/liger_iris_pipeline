Data Models
===========

Data models specify an interface between the data files and DRS. They ensure that the data files conform to a specific structure and contain the necessary information for processing. All data models are defined in the module :mod:`liger_iris_pipeline.datamodels`.

File format specification
-------------------------

All data will be stored in FITS file format, following similar conventions used by JWST, see https://jwst-docs.stsci.edu/understanding-data-files. The DRS team may choose to adopt non-FITS file formats for certain calibrations if appropriate.

The structure of all FITS files used by the DRS are encoded as schemas in YAML format in schema files. Schema files can also reference other schema files, for example, `core.schema.yaml <https://github.com/oirlab/liger_iris_pipeline/blob/4e85942b481ab948e0ea790b509432479d5bd6b9/liger_iris_pipeline/datamodels/schemas/core.schema.yaml#L4>`_ internally refernces several files. See the JWST documentation `here <https://stdatamodels.readthedocs.io/en/latest/jwst/datamodels/schemas.html#jwst-schemas>`_ for more information on schemas.

One crucial entry in the schema is meta.model_type, which is specified by the FITS header key ``DATAMODL``.

For example the data model for processed Imager frames is :py:class:`~liger_iris_pipeline.datamodels.ImagerModel`, and is referenced in the FITS keyword ``DATAMODL``::

    DATAMODL= 'ImagerModel'


Filenames
^^^^^^^^^

Standard Liger and IRIS files follow this naming convention

``{sem_id}-{program_number}-{obs_number}_{instrument}_{detector}_{exptype}_LVL{level}_{exp}-{subarray}.fits``

where:

- **sem_id**: The semester ID (*Example* ``2024B``)
- **program_number**: The program number (*Example* ``P123``)
- **obs_number**: The observation number (*Example* ``008``)
- **instrument**: The instrument name (*Example* ``IRIS``)
- **detector**: The detector name (*Example* ``IMG``, ``IMG1``, ``IFU``)
- **exptype**: The exposure type (*Example* ``SCI``, ``DARK``, ``SKY``)
- **level**: The data processing level (*Example* ``1``, ``2``)
- **exp**: The exposure number (*Example* ``0001``, ``0002``, ``IFU``)
- **subarray**: The subarray ID (*Example* ``00``, ``01``, ``02``)

*Example:*

2024B-P123-008_IRIS_IMG1_SCI_LVL0_0001-00.fits


Calibration files
+++++++++++++++++

Calibration files have their own format:

``{instrument}_{detector}_{reftype}_{date}_{version}.fits``

where:

- **instrument**: The instrument name (*Example* ``IRIS``)
- **detector**: The detector name (*Example* ``IMG``, ``IMG1``, ``IFU``)
- **reftype**: The reference file type (*Example* ``BIAS``, ``FLAT``)
- **date**: The ISO8601 timestamp for this reference file, corresponding to the start time of the first exposure that went into generating this calibration (*Example* ``20240101T000000``)
- **version**: The semver of the reference file, always starting at 0.0.1 (*Example* ``0.0.1``)

*Example:*

IRIS_IMG1_FLAT_20240101T000000_0.0.1.fits


Data levels
-----------

Science data
^^^^^^^^^^^^

* Level 0 (L0) data products are the FITS files containing the individual raw readouts.
* The stage 1 pipeline combines the raw readouts (L0) and applies data quality checks and cuts.
* The stage 1 pipeline then produces level 1 (L1) data products, the "raw science frames", still uncalibrated.
* Stage 2 pipelines apply calibration and additional standard routines (i.e. spectral extraction) to raw science frames (L1).
* The output of stage 2 pipelines are level 2 (L2) data products "reduced science frames"
* Multiple reduced science frames (L2) can be combined together by a stage 3 pipeline, for example for mosaicking.
* The outputs of stage 3 pipelines are L3 data products.

Calibration data
^^^^^^^^^^^^^^^^

Calibration data is generated with a custom calibration pipeline unique to that calibration. Calibration data products do not follow the same data level convention due to the specific nature of what their data product represents.


Metadata
--------

All metadata is specified via the data model `schemas <https://github.com/oirlab/liger_iris_pipeline/blob/4e85942b481ab948e0ea790b509432479d5bd6b9/liger_iris_pipeline/datamodels/schemas/>`_. Some of this metadata is injected by the DRS, while other metadata comes from instrument or observatory telemetry.

At TMT, telemetry from other subsystems is specified in the `DRS Assembly <https://github.com/tmt-icd/IRIS-Model-Files/tree/master/drs/drs-assembly>`.


Implement new datamodel
-----------------------

To implement a new datamodel, define a new class that inherits from :py:class:`~liger_iris_pipeline.datamodels.model_base.LigerIRISDataModel`, or from :py:class:`~liger_iris_pipeline.datamodels.referencefile.ReferenceFileModel` for a new reference file model.

For most datamodels, the only tasks are to create a new merged schema, and to specify this schema in the new datamodel class:

.. code-block:: python

    class MyCustomDataModel(ReferenceFileModel):
        """
        Summary of MyCustomDataModel.
        """
        schema_url = "https://oirlab.github.io/schemas/MyCustomDataModel.schema"



Create test data
----------------

To create a new FITS file for developing the DRP, see methods in :py:mod:`~liger_iris_pipeline.tests.utils`.