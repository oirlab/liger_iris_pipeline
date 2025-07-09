Bias
====

The bias level is the pixel dependent zero point offset added to the data by the detector control software.

**Classes:**

* :py:class:`~liger_iris_pipeline.datamodels.bias.BiasModel`

**Calibration type:** bias


Extensions
----------

.. csv-table::
   :header: "HDU Name", "HDU Type", "Data Type", "Dimensions", "Units", "Description"

   DATA, Image, Float32, "Ny x Nx", "e-/s", "Dark current data."
   ERR, Image, Float32, "Ny x Nx", "e-/s", "Dark current error."
   DQ, Image, UInt32, "Ny x Nx", None, "Data quality."