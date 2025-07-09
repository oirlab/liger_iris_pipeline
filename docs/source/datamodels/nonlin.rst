Non Linearity Correction
========================

Describes the nonlinearity of the detector readout response with a unique polynomial for each pixel.

**Classes:**

* :py:class:`~liger_iris_pipeline.datamodels.nonlin.NonlinearCorrectionModel`

**Calibration type:** nonlin


Extensions
----------

.. csv-table::
   :header: "HDU Name", "HDU Type", "Data Type", "Dimensions", "Units", "Description"

   COEFF, Image, Float32, "Ny x Nx x Ncoeff", "None", "Polynomial coefficients describing the linear response of the detector."