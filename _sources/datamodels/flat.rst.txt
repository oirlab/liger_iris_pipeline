Flat Field
==========

The flat field corrects for the pixel to pixel sensitivity.

**Classes:**

* :py:class:`~liger_iris_pipeline.datamodels.flat.FlatModel`

**Calibration type:** flat


Extensions
----------

.. csv-table::
   :header: "HDU Name", "HDU Type", "Data Type", "Dimensions", "Units", "Description"

   DATA, Image, Float32, "Ny x Nx", "e-/s", "Normalized flat field."
   ERR, Image, Float32, "Ny x Nx", "e-/s", "Normalized flat field errors."
   DQ, Image, UInt32, "Ny x Nx", None, "Data quality (:doc:`DQ flags <data_quality>`)."