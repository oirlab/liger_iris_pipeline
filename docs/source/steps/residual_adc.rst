Differential Atmospheric Dispersion Correction (ADC)
====================================================

Overview
--------

Corrects the residual atmospheric dispersion in the input data.


Algorithm
---------

If necessary, implement residual ADC module (TBD). The ADC corrects the for the refraction caused by the atmosphere, at varying airmasses (or elevation). If the residuals from ADC correction are significant (like 4th order), it may be necessary to implement a module. To calibrate it, on-sky tests are required. One such test is to use a star to map the dispersion through the system at varying airmasses. Once the system is calibrated, temperature and pressure from the local weather, dome, telescope and instrument can be incorporated into the correction of the residuals per wavelength of light. With temperature/pressure lookup table, the DRS will have the correct spectral trace for the extraction. See instrument dispersion for how this is dealt with internally.


Subarrays
---------

TBD


Arguments
---------

TBD

Reference Files
---------------

TBD