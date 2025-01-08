DRS-ROP Pipeline
================

The DRS_ROP Pipeline works on detector level readouts. The current steps implemented in the pipeline are
- Non-linearity Correction
- Detector Readout Sampling


Non-linearity Correction
------------------------
Non-linearity correction step corrects for the non-linear response of the detector to incoming flux. This step is executed before sampling algorithms.


Detector Readout Sampling
-------------------------
The H4RG detecors are readout in non-destructive reads and sampling algorithms are used to estimate the accumulated electrons in the detector for an integration time. The sampling algorithms currently implemented in the pipeline are
- (Multi)-Correlated Double Sampling
- Up-the-Ramp Sampling

Running the Examples
--------------------
There is a example run in the liger_iris_pipeline/readout directory. The sample ramp is given in the sample_ramp.fits.
sampling.cfg gives the configurations for the pipeline.

Execute the pipeline from the command line
------------------------------------------

We can use ``strun`` from a terminal to execute the pipeline:

::

   tmtrun sampling.cfg sample_ramp.fits

here is the output log:

.. code:: bash

	2019-04-26 10:09:21,309 - stpipe.rop - INFO - ROPPipeline instance created.
	2019-04-26 10:09:21,310 - stpipe.rop.nonlincorr - INFO - NonlincorrStep instance created.
	2019-04-26 10:09:21,311 - stpipe.rop.readoutsamp - INFO - ReadoutsampStep instance created.
	2019-04-26 10:09:21,311 - stpipe - INFO - Hostname: arun-ThinkPad-X1-Carbon-6th
	2019-04-26 10:09:21,311 - stpipe - INFO - OS: Linux
	2019-04-26 10:09:21,335 - stpipe.rop - INFO - Step rop running with args ('sample_ramp.fits',).
	2019-04-26 10:09:21,335 - stpipe.rop - INFO - Starting ROP Pipeline ...
	2019-04-26 10:09:21,499 - stpipe.rop.nonlincorr - INFO - Step nonlincorr running with args (<RampModel(1, 4, 10, 10) from sample_ramp.fits>,).
	2019-04-26 10:09:21,577 - stpipe.rop.nonlincorr - INFO - Step nonlincorr done
	2019-04-26 10:09:21,603 - stpipe.rop.readoutsamp - INFO - Step readoutsamp running with args (<RampModel(1, 4, 10, 10) from sample_ramp.fits>,).
	2019-04-26 10:09:21,618 - stpipe.rop.readoutsamp - INFO - MCDS Sampling Selected
	(10, 10)
	2019-04-26 10:09:21,640 - stpipe.rop.readoutsamp - INFO - Step readoutsamp done
	2019-04-26 10:09:21,665 - stpipe.rop - INFO - Saved model in sample_rop.fits
	2019-04-26 10:09:21,665 - stpipe.rop - INFO - Step rop done


This creates a sample_rop.fits file in the working directory that is the processed
