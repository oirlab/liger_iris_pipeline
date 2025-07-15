========
Raw Ramp
========

Liger and IRIS level 0 data (L0) are a set of up the ramp (UTR) images read out from the Hawaii 2- or 4-RG detectors. Imager and IFU level 0 data products use the same datamodel.


Extensions
----------

.. csv-table::
   :header: "HDU Name", "HDU Type", "Data Type", "Dimensions", "Units", "Description"

   DATA, Image, Float32, "Ny x Nx", e-, "Rate map."
   ERR, Image, Float32, "Ny x Nx", e-, "Rate map error (all sources)."
   DQ, Image, UInt32, "Ny x Nx", None, "Data quality (:doc:`DQ flags <data_quality>`)."