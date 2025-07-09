======================
Wavelength Calibration
======================

Description
-----------

TBD.


Algorithm
---------

Wavelength calibration is performed using on arc lamps taken during daytime calibrations, typically Ar, Kr, and Xe. The arc lamps provide better velocity resolution and stability over OH skylines. A global wavelength solution is found for all of the spectra by fitting a low order polynomial. Legendre polynomials are preferred as they can be inverted (i.e. wavelength(pixel) → pixel(wavelength)) without significant errors in the coefficients. Using the global solution, a solution is found for each spaxel (spatial pixel). The solutions will be resampled to a common linear wavelength scale. These solutions are found be fairly stable in OSIRIS and we expect them to be similar. We anticipate checking the solution monthly for any changes. The solutions will be static based on the input lamp spectra and date they were taken.


Subarrays
---------

TBD


Arguments
---------

TBD

Reference Files
---------------

TBD