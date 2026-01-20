============
Calibrations
============

*Under development as interfaces to KOA and TMT are being specified*


Calibration files
-----------------

Many DRS algorithms require additional calibration data products or telemetries not stored with the data product itself. This includes both on-sky data (that is not of the astronomical target itself), daytime calibration frames, and other sub-component metadata. Metadata is non-image information that will typically come from the header of raw FITS files, or from IRIS, and/or the adaptive optics system via the observatory telemetry service. The NFIRAOS Science Calibration Unit (NSCU) will include a calibration system that will facilitate the taking of daytime calibration frames, such as arc lamp spectra, white light flat field images, and pinhole grids for measuring distortion.  The following table summarizes the required calibration files necessary for the Data Reduction Software.

List of Calibrations
--------------------

See :doc:`../datamodels/datamodels` for additional details on each calibration. "Real Time" indicates whether or not the reference file can be acquired and created during on-sky operations.

.. csv-table::
   :header: "Name", "Reference Type", "Source", "Algorithms", "Real Time?"

   "Atm. Dispersion Residual","Metadata","IRIS ADC","Atmospheric Correction","Yes"
   "Arc lamp spectra*", "CAL (2D)","IRIS DTC (NSCU)","Wavelength solution ","Yes"
   ":py:class:`~liger_iris_pipeline.datamodels.dq.DQModel`","CAL (2D)","IRIS DTC","Correction of detector artifacts","Yes"
   ":py:class:`~liger_iris_pipeline.datamodels.dark.DarkModel`","CAL (2D)","IRIS DTC and NTC","Dark subtraction ","Yes"
   ":py:class:`~liger_iris_pipeline.datamodels.flat.FlatModel`","CAL (2D)","IRIS DTC and NTC","Flatfield correction","Yes"
   "Env metadata", "Metadata","ESW, FITS header","All","Yes"
   "Fiber image", "CAL (2D, 3D)","IRIS DTC (NSCU)","PSF Calibration","No"
   "Flux calibration star","CAL (2D, 3D)","IRIS On-sky","Extract Star, Remove Absorption Lines","No"
   "Instrument config","Metadata","ESW, FITS header","All","Yes"
   "Lenslet scan*", "Rect Matrix CAL (2D)","IRIS DTC (NSCU)","Spectral Extraction","No"
   "NFIRAOS config", "Metadata","ESW, FITS header","All","Yes"
   "Pinhole Grid (D-Map)","CAL (2D)","IRIS DTC (NSCU)","Field distortion correction","No"
   "PSF metadata","Metadata ","ESW, FITS header","PSF calibration","No"
   "PSF star","CAL (2D, 3D)","IRIS on-sky ","PSF calibration","No"
   "Sky frame","CAL (2D, 3D)","IRIS on-sky","Sky-subtraction","Yes"
   "Telescope config PTG","Metadata","ESW,FITS header","All", "Yes"