======================
Distortion Corrections
======================

Both corrections are implemented as `astropy distortion lookup tables <https://docs.astropy.org/en/stable/api/astropy.wcs.DistortionLookupTable.html>`_.

*Future versions may use the `astropy.modeling <https://docs.astropy.org/en/stable/modeling/index.html>_` module.*

The **instrinsic instrument distortion correction** is determined from the Zemax model of the integrated optics.

The **DAR correction** is determined from the local atmospheric conditions (temperature, pressure, humidity).

The combined distortion correction is applied in detector pixel coordinates. The image is resampled back onto the original pixel grid with `DrizzlePac <https://www.stsci.edu/scientific-community/software/drizzlepac>`_.

For IFS data, the corrections may be applied in the point cloud instead of a uniformly sampled cube.