====
Flat
====

The flat field corrects for the pixel to pixel sensitivity.


Extensions
----------

.. csv-table::
   :header: "#", "Name", "HDU TYPE", "Data Type", "Dimensions", "Units", "Description"

   1, DATA, Image, Float32, "4096 x 4096", "None (normalized)", "Flat field data."
   2, ERR, Image, Float32, "4096 x 4096", "None (normalized)", "Flat field error (all sources)."
   5, DQ, Image, UInt32, "4096 x 4096", None, "Data quality."