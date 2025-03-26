============================
Nonlinear Readout Correction
============================


Description
-----------

The step :py:class:`~liger_iris_pipeline.readout.nonlincorr_step.NonlinearCorrectionStep` divides a sequence of UTR reads by the nonlinear detector response.


Algorithm
---------

The pre-calcualted nonlinearity response will be modeled with a polynomial and computed in :py:class:`~liger_iris_pipeline.pipeline.calc_nonlincorr.CalcNonLinearResponse` (*under development*).


Subarrays
---------

If nonlinearity is subarray-dependent.


Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.ramp.RampModel`
    The input file or ramp model to process.

**nonlincoeff** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.nonlin_readout_params.NonlinearReadoutParametersModel` | ``None``
    The name of the nonlincoeff reference file or non linear parameters model to use. If not provided, the nonlincoeff model is queried from CRDS.



Reference Files
---------------

**nonlincoeff** : Nonlinear coefficients.
