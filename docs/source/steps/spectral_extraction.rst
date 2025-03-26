===================
Spectral Extraction
===================

Description
-----------

TBD.


Algorithm
---------

Lenslet: Flux from an individual lenslet will be spread out into neighboring lenslets. Depending on the spacing between the lenslets, will determine how much flux falls into a neighboring lenslet. In order to recover the flux for an individual lenslet, it will be necessary to perform a deconvolution on the entire lenslet array, assigning flux to the appropriate lenslet. OSIRIS uses the Gauss-Seidel method to iteratively assign flux to individual spatial pixels (spaxels; Krabbe et al. 2004). The biggest assumption of the method is the knowledge of the PSF. In order to mitigate this problem, the PSF needs to be mapped in 2D and the structure of each lenslets PSF needs to be known precisely. Thus, the spectral extraction requires additional calibration files, rectification matrix (rectmat), which contains information about each lenslets PSF as a function of wavelength. Additional methods may be needed during INT.

Slicer: Spectral extraction of the slicer will be similar to MOS (multi-object spectroscopy). The trace of each spectrum will be performed, typically fitting a low order polynomial. An aperture will be used over the spectrum, optimizing signal-to-noise (Horne 1986). The extraction will be highly dependent on the extraction region and sky-subtraction algorithms.


Subarrays
---------

TBD


Arguments
---------

TBD

Reference Files
---------------

TBD