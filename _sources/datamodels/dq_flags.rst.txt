Data quality (DQ) flags
=======================

The data quality flags describe the quality of a given pixel. A static DQ Model is used to initialize the DQ attribute in each data model. Values in the DQ array can be any valid unsigned integer where each bit represents whether that DQ flag is true (1) or false (0). If all bits are zero, the pixel is considered good.

**Classes:**

* :py:class:`~liger_iris_pipeline.datamodels.dark.DarkModel`

**Calibration type:** dark


Extensions
----------

.. csv-table::
   :header: "HDU Name", "HDU Type", "Data Type", "Dimensions", "Units", "Description"

   DQ, Image, UInt32, "Ny x Nx", None, "Data quality."


.. csv-table::
   :header: "Bit", "Value", "Name", "Description"

   "-", "0", "GOOD", "Good pixel."
   "0", "1", "DO_NOT_USE", "Bad pixel. Do not use"
   "1", "2", "SATURATED", "Pixel saturated during exposure"
   "2", "4", "JUMP_DET", "Jump detected during exposure"
   "3", "8", "OUTLIER_MID_TIME", "Mid exposure time is outlier in spectral order"
   "4", "16", "OUTLIER", "Flagged by outlier detection"
   "5", "32", "PERSISTENCE", "Pixel exhibiting high persistence"
   "6", "64", "TBD", ""
   "7", "128", "TBD", ""
   "8", "256", "UNRELIABLE_ERROR", "Uncertainty exceeds quoted error"
   "9", "512", "NON_SCIENCE", "Pixel not on science portion of detector"
   "10", "1024", "DEAD", "Dead pixel"
   "11", "2048", "HOT", "Hot pixel"
   "12", "4096", "WARM", "Warm pixel"
   "13", "8192", "LOW_QE", "Low quantum efficiency"
   "14", "16384", "TBD", ""
   "15", "32768", "TELEGRAPH", "Telegraph pixel"
   "16", "65536", "NONLINEAR", "Pixel highly nonlinear"
   "17", "131072", "BAD_REF_PIXEL", "Reference pixel cannot be used"
   "18", "262144", "CROSS_BAD", "Center of cross-shaped bad pixel"
   "19", "524288", "CROSS_BAD_NEIGH", "Neighbor of cross-shaped bad pixel"
   "20", "1048576", "TBD", ""
   "21", "2097152", "TBD", ""
   "22", "4194304", "UNRELIABLE_BIAS", "Bias variance large"
   "23", "8388608", "UNRELIABLE_DARK", "Dark variance large"
   "24", "16777216", "UNRELIABLE_SLOPE", "Slope variance large"
   "25", "33554432", "UNRELIABLE_FLAT", "Flat variance large"
   "26", "67108864", "UNRELIABLE_WS", "Unreliable wavelength solution"
   "27", "134217728", "LOW_INST_TRANS", "Low instrument transmission (blaze < ~90%)"
   "28", "268435456", "TELLURIC", "Telluric absorption line"
   "29", "536870912", "OH_LINE", "OH emission line"
   "30", "1073741824", "OTHER_BAD_PIXEL", "A catch-all flag"
   "31", "2147483648", "REFERENCE_PIXEL", "Pixel is a reference pixel"

