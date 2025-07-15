Nonlinear Readout Correction
============================


Overview
--------

The step divides a sequence of UTR reads by the nonlinear detector response.

**Class**: :py:class:`~liger_iris_pipeline.readout.nonlincorr_step.NonlinearCorrectionStep`


Algorithm
---------

The data is transformed with a polynomial which describes the nonlinear response of the detector.


Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.ramp.RampModel`
    The input file or ramp model to process.

**nonlin** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.nonlin.NonlinearCorrectionModel` | ``None``
    The name of the nonlin reference file or non linear parameters model to use. If not provided, the calibration is retrieved from the appropriate archive.



Subarrays
---------

TBD



Calibration Files
-----------------

**nonlin** : Nonlinear calibration file.
