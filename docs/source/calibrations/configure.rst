=========
Configure
=========

The middleware can be used locally if you only need to access cached calibration files. However, to retrieve new calibrations from the Keck Observatory Archive (KOA), you will need to connect to the remote KOA calibration database. For now, this is hosted at Keck Observatory.

See the `KOA Middleware documentation <https://oirlab.github.io/KOA_Middleware/authentication.html>`_ for details on setting up authentication to access KOA/Keck remotely.

Calibration Cache
-----------------

The local calibration cache must have the directory structure below. Any sub-folders will be created if they do not exist. The default local SQLite database is named ``<instrument_name>_calibrations.db`` where ``instrument_name`` will be ``liger`` for Liger calibrations and be located in the ``database/`` subdirectory. 

Liger calibration files are located in ``calibrations/liger`` subdirectory.

.. code-block:: text

    /koa_calibration_cache/
    ├── calibrations/
    │   └── liger/
    │       ├── liger_cal1.fits
    │       ├── liger_cal2.fits
    │       └── ...
    └── database/
        └── liger_calibrations.db



Environment Variables
---------------------

The following environment variables can be set to configure the calibration data management:

- **KOA_CALIBRATION_CACHE** (Required)
  Path to cached calibrations directory.

- **KOA_LOCAL_DATABASE_FILENAME** (Optional)
  Local SQLite database filename. Default: ``<instrument_name>_calibrations.db``. Full path is determined by this and the ``KOA_CALIBRATION_CACHE`` environment variable.

- **KOA_USE_CACHED_CALIBRATIONS** (Optional)
  Use cached files ('true' or 'false'). Default: 'true'.

- **KOA_LOCAL_DATABASE_TABLE_NAME** (Optional)
  Local database table name. Default: ``liger``

- **KOA_CALIBRATIONS_URL** (Optional)
  Remote database URL. Default: Keck Observer API URL. Default is "https://www3.keck.hawaii.edu/api/calibrations", and will be replaced with the appropriate KOA URL in the future.

- **KOA_CALIBRATION_ORIGIN** (Optional)
  **BEHAVIOR UNDER DEVELOPMENT AND SUBJECT TO CHANGE**
  Behavior for selecting calibrations for processing, and for registering new calibrations to the local database. Options are: "KECK", "LOCAL".