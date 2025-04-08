====
Dark
====

The dark current (and any other contribution to the dark) is assumed to be linear with time.


Extensions
----------

.. csv-table::
   :header: "#", "Name", "HDU TYPE", "Data Type", "Dimensions", "Units", "Description"

   1, DATA, Image, Float32, "4096 x 4096", "e/s", "Dark current data."
   2, ERR, Image, Float32, "4096 x 4096", "e/s", "Dark current error (all sources)."
   5, DQ, Image, UInt32, "4096 x 4096", None, "Data quality."