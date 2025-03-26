Description
===========

Algorithm
---------

The dark current step removes dark current from a exposure by subtracting
dark current data stored in a dark reference file.

The dark reference file data
are directly subtracted from the science exposure.

The frame-averaged dark is constructed using the following scheme:

* SCI arrays are computed as the mean of the original dark SCI arrays
* ERR arrays are computed as the uncertainty of the mean, using
  :math:`\frac{\sqrt {\sum \mathrm{ERR}^2}}{nframes}`

Any pixel values in the dark reference data that are set to NaN will have their
values reset to zero before being subtracted from the science data, which
will effectively skip the dark subtraction operation for those pixels.

The dark DQ array is combined with the science exposure PIXELDQ array using a
bitwise OR operation.

**Note**: If the input science exposure contains more frames than the available
dark reference file, no dark subtraction will be applied and the input data
will be returned unchanged.

Subarrays
---------

It is assumed that dark current will be subarray-dependent, therefore this
step makes no attempt to extract subarrays from the dark reference file to
match input subarrays. It instead relies on the presence of matching subarray
dark reference files in CRDS.
