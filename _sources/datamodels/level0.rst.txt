==============
Level 0 (Ramp)
==============

Liger and IRIS level 0 data (L0) are a set of UTR images read out from the Hawaii 2- or 4-RG detectors. Imager and IFU level 0 data products use the same datamodel.


Extensions
----------

.. csv-table:: 
   :header: "#", "Name", "HDU Type", "Data Type", "Dimensions", "Units", "Description"

   "1", "SCI", "Image", "Float32", "Ny x Nx x Ngroups x Nreads", "e-/s", "Individual reads split by groups."
   "2", "TIMES", "Table", "See below", "See below", "See below", "Start time of each read."
   "3", "PIXEL_DQ", "Image", "Uint32", "Ny x Nx", "N/A", "Data quality for groups."
   "4", "GROUP_DQ", "Image", "Uint32", "Ny x Nx x Ngroups x Nreads", "N/A", "Data quality for each group of reads."
