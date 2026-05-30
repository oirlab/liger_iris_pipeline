============
Calibrations
============

Overview
--------

Many DRS algorithms require additional calibration data products or telemetries not stored with the data product itself. This includes both on-sky data (that is not of the astronomical target itself), daytime calibration frames, and other sub-component metadata. Metadata is non-image information that will typically come from the header of raw FITS files, or from instrument, and/or the adaptive optics system via the observatory telemetry service.

The NFIRAOS Science Calibration Unit (NSCU) for IRIS at TMT will include a calibration system that will facilitate the taking of daytime calibration frames, such as arc lamp spectra, white light flat field images, and pinhole grids for measuring distortion. The following table summarizes the required calibration files necessary for the Data Reduction Software.

The :py:mod:`calibrations` module contains code to:

1. Interact with a local calibration cache that stores Liger and IRIS calibration files and uses an SQLite database to interact with the calibration metadata.
2. Select the appropriate calibration file for a given input based on the metadata and instrument configuration using SQL queries and Python filtering.
3. Download new calibration metadata entries from KOA as new calibrations are created from the main DRP running at Keck.
4. Register new custom calibrations to the local cache after they are created by the DRP.
5. Upload new calibration files and metadata to the remote KOA database after they are created by the DRP (*restricted access*).

Observatory Middleware
----------------------

In order to select and retrieve calibrations for processing, liger_iris_pipeline interacts with the appropriate observatory's middlware.

For Liger/Keck, this is `KOA Middleware <https://oirlab.github.io/KOA_Middleware/>`_. This package can download calibration files from the Keck Observatory Archive (KOA) and provides a local cache for calibration files. koa_middleware also provides the framework for matching calibration files to science data products based on metadata.

See `KOA Middleware Documentation <https://oirlab.github.io/KOA_Middleware/index.html>`_ for more information.

The IRIS/TMT middleware is still under development but will serve the same functionality as koa_middleware.

**The KOA Middleware quickstart and liger_iris_pipeline quickstarts both go over common use cases of working with calibration data:**

- `KOA Middleware Quickstart <https://oirlab.github.io/KOA_Middleware/quickstart.html>`_.

- :doc:`liger_iris_pipeline Calibration Examples <../quickstart/calibration_examples>`.

In the sections below, we provide an overview of using the calibration database in the context of the liger_iris_pipeline, and link to the KOA Middleware documentation where appropriate.

.. toctree::
   :maxdepth: 2
   :glob:

   configure
   calibration_database

List of Calibrations
--------------------

The following table lists the calibration files used within the DRS. "Real Time" indicates whether or not the reference file can be acquired and created during on-sky operations.

.. csv-table::
   :header: "Name", "Reference Type", "Liger Source", "IRIS Source", "Algorithms", "Real Time?"

   "Atm. Dispersion Residual","Metadata","IRIS ADC","Liger ADC","Atmospheric Correction","Yes"
   "Arc lamp spectra*", "CAL (2D)","IRIS DTC (NSCU)","IRIS DTC (NSCU)","Wavelength solution ","Yes"
   "`DQModel`","CAL (2D)","IRIS DTC","IRIS DTC","Correction of detector artifacts","Yes"
   "`DarkModel`","CAL (2D)","IRIS DTC and NTC","IRIS DTC and NTC","Dark subtraction ","Yes"
   "`DetectorFlatModel`","CAL (2D)","IRIS DTC and NTC","IRIS DTC and NTC","Detector flat correction","Yes"
   "Env metadata", "Metadata","ESW, FITS header","ESW, FITS header","All","Yes"
   "Fiber image", "CAL (2D, 3D)","IRIS DTC (NSCU)","IRIS DTC (NSCU)","PSF Calibration","No"
   "Flux calibration star","CAL (2D, 3D)","IRIS On-sky","IRIS On-sky","Extract Star, Remove Absorption Lines","No"
   "Instrument config","Metadata","ESW, FITS header","ESW, FITS header","All","Yes"
   "Lenslet scan*", "Rect Matrix CAL (2D)","IRIS DTC (NSCU)","IRIS DTC (NSCU)","Spectral Extraction","No"
   "NFIRAOS config", "Metadata","ESW, FITS header","ESW, FITS header","All","Yes"
   "Pinhole Grid (D-Map)","CAL (2D)","IRIS DTC (NSCU)","IRIS DTC (NSCU)","Field distortion correction","No"
   "PSF metadata","Metadata ","ESW, FITS header","ESW, FITS header","PSF calibration","No"
   "PSF star","CAL (2D, 3D)","IRIS on-sky ","IRIS on-sky ","PSF calibration","No"
   "Sky frame","CAL (2D, 3D)","IRIS on-sky","IRIS on-sky","Sky-subtraction","Yes"
   "Telescope config PTG","Metadata","ESW,FITS header","ESW,FITS header","All", "Yes"