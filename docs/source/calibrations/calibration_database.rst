====================
Calibration Database
====================

Overview
--------

liger_iris_pipeline uses a local calibration database to manage calibration files and metadata. This database is implemented as a local SQLite database that interacts with a cache of calibration files stored on disk.

Liger Calibration Store
-----------------------

The `LigerCalibrationStore` class provides the main interface for working with the calibration database in the context of Liger.

An analogous class for IRIS is under development but will provide the same functionality.

Calibration Versioning
----------------------

Each calibration file is associated with a version, which is determined by the metadata of the calibration file. Version numbers start at "001" and increment for each "new version of that same calibration" up to "999".

Version Family
++++++++++++++

From a versioning context, calibration files are determined to be otherwise "identical" if they have the same values for a subset of metadata called the "version family".

The method :py:meth:`get_version_family_values` returns a list of database column names that are used to determine the version family.

For Liger, this is set to the following metadata keys:

- **Calibration Type**: ``cal_type`` (``meta.cal_type``)
- **Date time of observation**: ``datetime_obs`` (``meta.datetime_obs``)
- **Master Calibration**: ``master_cal`` (``meta.master_cal``)
- **Instrument Mode**: ``instrument_mode`` (``meta.instrument.mode``)
- **IFS Mode**: ``ifs_mode`` (``meta.ifs.mode``)


**If two calibration files have the same values for all of the version family metadata keys and have the same origin (See below), then they are considered to be "the same calibration" and must therefore have unique version numbers for both to exist in the database simultaneously.**

Calibration Origin
------------------

**!! NOTE !! - The behavior of ORIGIN is still being finalized subject to change. When creating new calibrations, populating the local/remote database, explicitly set the origin as needed.**

The origin defines the source of where the calibration came from, and provides an independent local-only namespace for assigning versions to calibration files:

- **KECK**: Calibrations generated at Keck which go through KOA.
- **LOCAL**: Calibrations that are generated manually within liger_iris_pipeline by the user which do not appear on KOA.

ORIGIN information is stored in the FITS metadata and used during version generation and file registration.

One can set the origin value globally with the ``KOA_CALBRATION_ORIGIN`` environment variable.

Important methods that interact with the origin include:

.. autoclass:: liger_iris_pipeline.calibrations.register_calibration_step.RegisterCalibrationStep
    :noindex:
    :members:
    :undoc-members:

.. automethod:: liger_iris_pipeline.calibrations.liger_store.LigerCalibrationStore.register_calibration
    :noindex:

.. automethod:: liger_iris_pipeline.calibrations.liger_store.LigerCalibrationStore.sync_records_from_cached_files
    :noindex:

.. automethod:: liger_iris_pipeline.calibrations.liger_store.LigerCalibrationStore.generate_calibration_version
    :noindex: