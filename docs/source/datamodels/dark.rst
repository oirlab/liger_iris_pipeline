Dark
====

The dark current (and any other contribution to the dark) is assumed to be linear with time and is stored as a rate map product (e-/s).

**Classes:**

* :py:class:`~liger_iris_pipeline.datamodels.dark.DarkModel`

**Calibration type:** dark


Extensions
----------

.. csv-table::
   :header: "HDU Name", "HDU Type", "Data Type", "Dimensions", "Units", "Description"

   DATA, Image, Float32, "Ny x Nx", "e-/s", "Dark current data."
   ERR, Image, Float32, "Ny x Nx", "e-/s", "Dark current error."
   DQ, Image, UInt32, "Ny x Nx", None, "Data quality (:doc:`DQ flags <data_quality>`)."