Flux Calibration
================


Overview
--------

Subtracts the dark current from the input data.


**Class**: TBD


Algorithm
---------

Imager: To convert from DN to flux (erg/s/cm^2/Hz) or AB magnitude a standard star needs to be observed in the same instrument configuration, airmass, and close in time as the science observations.

For science fields and filters that overlap with SDSS (citation), Pan-STARRS (citation) or UKIDDS (citation) will be able to use the stars within the science frame for as standards (2MASS may be too bright and low resolution to use). For science fields outside these surveys or for more precise photometry will require observing a standard star from a standard field. Apertures of increasing radii will be used to determine the curve of growth and the appropriate aperture to use with the PSF and seeing, maximizing S/N. Once an aperture size is determined, the flux is integrated the flux for a given band to produce the flux of the star in DN. Aperture corrections will be applied based PSF and the seeing. For relative photometry, :math:m_1-m_2=-2.5log_{10}\left(i \dfrac{f_1}{f_2}\right), where m1 and m2 are magnitudes of the sources and f1 and f1 are fluxes of the sources. This can be performed with a single source or the entire field with known sources to scale image. The zeropoints of the image can be determined from the known sources integrated flux and magnitude, (i.e. :math:m=-2.5log_{10}\left( \dfrac{DN}{exptime}\right)+zeropoint). On sky tests will be required to determine the extinction corrected instrumental zeropoints.

IFS: To convert from DN to flux units (erg/s/cm^2/Ang) a standard star needs to be observed in the same instrument configuration, airmass,and close in time as the science observations. In the near-IR the standard star at minimum needs to have zJHK photometry or ideally a spectrophotometric standard (in which a calibrated spectrum already exists). For a standard star with zJHK photometry, the photometry will be fit with a Planck law (or Rayleigh-Jeans approximation :math:1/\lambda^4). Apertures of increasing radii will be used to determine the curve of growth and the appropriate aperture to use with the PSF and seeing. Once an aperture size is determined, the flux is integrated for a given wavelength to produce the spectrum of the standard star in DN. Aperture corrections based on the with growth curve and imager data. The science data cube and standard data cube are normalized by the exposure time such that they are each DN/s (count rate). | For the standard, we take the ratio of the flux (ergs/s/cm^2/Ang) over the count rate (DN/s). Each spaxel in the science data cube is multiplied by the ratio (flux/count rate) from the standard :math:F_{sci}=\dfrac{F_{std}}{R_{std}}*R_{sci} , where F is flux (erg/s/cm^2) and R is count rate (DN/s).

Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.imager.ImagerModel` | :py:class:`~liger_iris_pipeline.datamodels.ifu.IFUCubeModel`
    The input data to calibrate the flux for.

Subarrays
---------

TBD

Calibration Files
-----------------

TBD