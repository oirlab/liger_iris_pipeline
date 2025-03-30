===================
Telluric Correction
===================

Description
-----------

TBD.


Algorithm
---------

Telluric absorption is caused by the Earths atmosphere, in which all spectra are attenuated by it. In order to correct for it, typically a featureless star is used to measure the attenuation carefully and apply a correction to the science spectra. Telluric correction as outlined by Vacca et al. 2003:

1. Normalization of the observed A-type main sequence star spectrum (e.g. O, B, and A should be fine with “featureless” spectra, as well as white dwarfs) in the vicinity of a suitable absorption feature (as defined below);

2. Determination of the radial velocity shift of the A-type star;

3. Shifting the Vega model spectrum to the radial velocity of the A-type star;

4. Scaling and reddening the Vega model spectrum to match the observed magnitudes of the A-type star;

5. Construction of a convolution kernel from a small region around an absorption feature in the normalized observed A-type and model Vega spectra;

6. Convolution of the kernel with the shifted, scaled, and reddened model of Vega;

7. Scaling the equivalent widths of the various H lines to match those of the observed A-type star.

Finally, the convolved model is divided by the observed A-type spectrum and the resulting telluric correction spectrum is multiplied by the observed target spectrum.


Subarrays
---------

TBD


Arguments
---------

TBD

Reference Files
---------------

TBD