=======================
Data quality (DQ) flags
=======================

Below are the data quality flags to label the quality of a given detector pixel or IFU spaxel. The flags are stored in the DQ extension of a FITS file. The flags are stored as a 32-bit integer, with each bit representing a different flag.

.. csv-table::
   :header: "Bit", "Name", "Description"

   "0", "DO_NOT_USE", "Bad pixel. Do not use"
   "1", "SATURATED", "Pixel saturated during exposure"
   "2", "JUMP_DET", "Jump detected during exposure"
   "3", "OUTLIER_MID_TIME", "Mid exposure time is outlier in spectral order"
   "4", "OUTLIER", "Flagged by outlier detection"
   "5", "PERSISTENCE", "Pixel exhibiting high persistence"
   "6", "TBD", ""
   "7", "TBD", ""
   "8", "UNRELIABLE_ERROR", "Uncertainty exceeds quoted error"
   "9", "NON_SCIENCE", "Pixel not on science portion of detector"
   "10", "DEAD", "Dead pixel"
   "11", "HOT", "Hot pixel"
   "12", "WARM", "Warm pixel"
   "13", "LOW_QE", "Low quantum efficiency"
   "14", "TBD", ""
   "15", "TELEGRAPH", "Telegraph pixel"
   "16", "NONLINEAR", "Pixel highly nonlinear"
   "17", "BAD_REF_PIXEL", "Reference pixel cannot be used"
   "18", "CROSS_BAD", "Center of cross-shaped bad pixel"
   "19", "CROSS_BAD_NEIGH", "Neighbor of cross-shaped bad pixel"
   "20", "TBD", ""
   "21", "TBD", ""
   "22", "UNRELIABLE_BIAS", "Bias variance large"
   "23", "UNRELIABLE_DARK", "Dark variance large"
   "24", "UNRELIABLE_SLOPE", "Slope variance large"
   "25", "UNRELIABLE_FLAT", "Flat variance large"
   "26", "UNRELIABLE_WS", "Unreliable wavelength solution"
   "27", "LOW_INST_TRANS", "Low instrument transmission (blaze < ~90%)"
   "28", "TELLURIC", "Telluric absorption line"
   "29", "OH_LINE", "OH emission line"
   "30", "OTHER_BAD_PIXEL", "A catch-all flag"
   "31", "REFERENCE_PIXEL", "Pixel is a reference pixel"
