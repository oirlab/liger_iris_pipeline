=============
Data Handling
=============

Open Model
++++++++++

The method :py:meth:`open` reads in a file and constructs the appropriate data model class for that data product as specified by the header key ``'DATAMODL'``.

**Data arrays** are accessed with ``model.<attribute>`` where the attribute name is the extension name (case insensitive).

**Metadata** is accessed with ``model.meta.<attribute>`` or ``model.meta.<section>.<attribute>`` according to datamodel schemas.

.. code-block:: python

    from liger_iris_pipeline import datamodels
    from liger_iris_pipeline.utils import download_gdrive_file
    sci_path = download_gdrive_file('')
    model = datamodels.open(sci_path)
    print(model.meta.datetime_obs) # -> '2023-10-06T00:00:00.000'
    print(model.meta.model_type) # -> 'L0Model'
    print(model.meta.exposure.type) # -> 'SCI'
    print(model.meta.instrument.mode) # -> 'IMG'
    print(model.shape) # -> (2048, 2112)

.. autofunction:: liger_iris_pipeline.datamodels.open


A file can also be passed to the constructor for the appropriate datamodel class:

.. code-block:: python

    from liger_iris_pipeline import datamodels
    model = datamodels.ImagerModel(sci_path)

.. autofunction:: liger_iris_pipeline.datamodels.LigerIRISDataModel.__init__

Save Model
++++++++++

Saving a datamodel is done with :py:meth:`~liger_iris_pipelline.datamodels.LigerIRISDataModel.save`. Existing files are always overwritten.

.. code-block:: python

    from liger_iris_pipeline import datamodels
    model = datamodels.open(sci_path)
    model.save(sci_path.replace('.fits', '_copy.fits'))

.. autofunction:: liger_iris_pipeline.datamodels.LigerIRISDataModel.save


Instantiate DataModel from Scratch
++++++++++++++++++++++++++++++++++

Instead of reading in a datamodel from a file, one can instantiate a datamodel from scratch.

.. code-block:: python

    from liger_iris_pipeline import datamodels
    model = datamodels.ImagerModel(
        date=np.ones((4096, 4160), dtype=np.float32),
        meta={
            'datetime_obs': '2024-09-24T00:00:00.000',
            'exposure.type': 'DARK'
        }
    )


**NOTE**: When instantiating new datamodels without a file, one should at minimum pass the ``datetime_obs`` or ``mjd_start`` keywords to the metadata.

Processing History
++++++++++++++++++

Each datamodel has a **receipt** attribute which is a Table that contains a history of all primitives that have been applied to the datamodel.

Processing history is always added to the output model(s).

* **CLASS** — Primitive class
* **PROC_START_TIME** — Processing start time YYYY-MM-DDTHH:MM:SS.sss
* **PROC_END_TIME** — Processing end time YYYY-MM-DDTHH:MM:SS.sss
* **FILENAME** — Base filename
* **PARAMETERS** — JSON representation of arguments
* **DRP_VERSION** — DRP semver
* **DRP_GIT_COMMIT_ID** — Full SHA1 commit ID
* **STATUS** — COMPLETED, FAILED, SKIPPED


Calibration History
+++++++++++++++++++

Each datamodel has a **calibrations** attribute which is a Table that contains a history of all calibrations that have been used within the context of this datamodel. Typically this means the calibration was 'applied' to the datamodel in some way, but it can also be used to track calibrations that were used in the creation of this datamodel, for example using an existing calibration as an initial guess to create a new calibration.

* **CAL_ROLE** — Role of calibration
* **CAL_TYPE** — Type of calibration
* **FILENAME** — Base filename of the calibration
* **ID** — UUID
* **DATETIME_OBS** — Observation date/time of the calibration.
* **LAST_PROCESSED** — When calibration was last processed.
* **TIME_APPLIED** — Time calibration was applied YYYY-MM-DDTHH:MM:SS.sss
* **CLASS** — Primitive class that used the calibration.
* **DRP_VERSION** — DRP semver calibration was processed with



Data Ancestors
++++++++++++++

**This is replaced with HDRTab, OBSOLETE**

Each datamodel has a **data_ancestors** attribute which is a Table that contains the datamodels which were used to create this datamodel in contexts such as coadding.

The default columns are:

* **FILENAME** - Base filename of the ancestor datamodel
* **CLASS** - The class of the ancestor
* **TIME_APPLIED** - The time this ancestor was used.
* ... plus other metadata fields as configured by ``include_ancestors`` in the metadata schema.

Additional columns are controlled through the metadata schema attributes ``include_ancestors=true/false``.



Switching between Liger and IRIS
++++++++++++++++++++++++++++++++

liger_iris_pipeline supports both Liger and IRIS data products. By default, the DRP assumes all data products are from Liger. Changing to IRIS data products can be done by setting the environment variable ``LIGERDRP_INSTRUMENT_NAME`` to ``'IRIS'``.

.. code-block:: bash

    export LIGERDRP_INSTRUMENT_NAME=IRIS

or in Python:

.. code-block:: python

    import os
    os.environ['LIGERDRP_INSTRUMENT_NAME'] = 'IRIS'

Each datamodel instance has an attribute ``config`` which is a Python class (not instance) that contains any instrument specific configuration and additional defaults not specified in the metadata schemas.