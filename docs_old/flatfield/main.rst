Description
===========
At its basic level this step flat-fields an input science data set by dividing
by a flat-field reference image. In particular, the SCI array from the
flat-field reference file is divided into both the SCI and ERR arrays of the
science data set, and the flat-field DQ array is combined with the science DQ
array using a bit-wise OR operation.

For pixels whose DQ is NO_FLAT_FIELD in the reference file, the flat
value is reset to 1.0. Similarly, for pixels whose flat value is NaN, the flat
value is reset to 1.0 and DQ value in the output science data is set to
NO_FLAT_FIELD. In both cases, the effect is that no flat-field is applied.

If any part of the input data model gets flat-fielded,
the status keyword S_FLAT will be set to
COMPLETE in the output science data.

Subarrays
---------
*Untested in liger_iris_pipeline*
This step handles input science exposures that were taken in subarray modes in
a flexible way. If the reference data arrays are the same size as the science
data, they will be applied directly. If there is a mismatch, the routine will
extract a matching subarray from the reference file data arrays and apply them
to the science data. Hence full-frame reference files can be
used for both full-frame and subarray science exposures, or subarray-dependent
reference files can be provided if desired.
