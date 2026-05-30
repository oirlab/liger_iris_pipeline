=========================
Working with Calibrations
=========================

The primary object for handling calibrations in the DRP is the :py:class:`~hispecdrp.calibrations.hispec_store.HISPECCalibrationStore` class, which provides an interface for registering, querying, and retrieving calibration files from the local cache and remote database on KOA. The store uses a local SQLite database to keep track of all available calibration metadata both local and from KOA.

**1. Construct a local SQLite DB from an existing cache directory.**

**Directory setup**: For this example, you must have a local cache directory with the following structure where <instrument_name> is the name of the instrument (lowercase).

.. code-block:: none

    /cache_dir/
    └── <instrument_name>/
        ├── cal_file1.fits
        ├── cal_file2.fits
        └── ...


.. code-block:: python

    from hispecdrp import RegisterCalibrationPrimitive
    from hispecdrp import datamodels

    # Astropy to get a simple cache directory for this example
    from astropy.utils.data import _get_download_cache_loc
    import os

    os.environ['KOA_CALIBRATION_CACHE'] = os.path.join(
        str(_get_download_cache_loc()),
        'hispecdrp_calibration_cache'
     ) + os.sep

    # Open dark model
    dark_path = download_gdrive_file('HB.20260212.00000.00.mastercal-dark.001.fits')
    dark_model = datamodels.open(dark_path)

    # Store the dark model in the local cache
    prim = RegisterCalibrationPrimitive()
    prim.apply(dark_model)

**2. Select and Retrieve a calibration with a Primitive.**

This will use the default calibration selector associated with the primitive (see primitive class).

.. code-block:: python

    from hispecdrp import DarkSubtractionPrimitive

    # Open science model
    sci_path = download_gdrive_file('HB.20231006.00000.00_rate-TELLURICS-FIB1.fits')
    sci_model = datamodels.open(sci_path)

    # Automatically select and retrieve a dark calibration using the DarkSubtractionPrimitive
    dark_prim = DarkSubtractionPrimitive()
    dark_path, dark_record = dark_prim.get_calibration(sci_model, 'dark')

**2. Select and Retrieve a calibration with the Calibration Store.**

This will specify the calibration selector to use. See `Calibration Selectors Documentation <https://oirlab.github.io/KOA_Middleware/selectors.html>`_ for more details.

.. code-block:: python

    from hispecdrp.calibrations import HISPECCalibrationStore, DarkSelector

    # Open science model
    sci_path = download_gdrive_file('HB.20231006.00000.00_rate-TELLURICS-FIB1.fits')
    sci_model = datamodels.open(sci_path)
    
    # Alternatively, query for a dark calibration using the CalibrationStore directly using a custom selector
    with HISPECCalibrationStore() as store:
        dark_path = store.get_calibration(sci_model, selector=DarkSelector())