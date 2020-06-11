DRS-ROP Pipeline
==========================

The DRS_ROP Pipeline works on detector level readouts. The current steps implemented in the pipeline are
- Non-linearity Correction
- Detector Readout Sampling


Non-linearity Correction
------------------------
Non-linearity correction step corrects for the non-linear response of the detector to incoming flux. This step is executed before sampling algorithms.


Detector Readout Sampling 
------------------------
The H4RG detecors are readout in non-destructive reads and sampling algorithms are used to estimate the accumulated electrons in the detector for an integration time. The sampling algorithms currently implemented in the pipeline are
- Correlated Double Sampling
- Multi Correlated Double Sampling
- Up-the-Ramp Sampling
 
Requirements
------------
You need following packages to run ROP pipeline

libcfitsio
cython

Install the iris_pipeline using 

.. code-block:: ini

	git clone --recurse-submodules https://github.com/arunsurya77/iris_pipeline



Running the Examples
---------------------
There is a example run in the iris_pipeline/readout/tests directory. The sample ramp is given in the sample_ramp_new.fits. This file can be extracted from `Figshare <https://figshare.com/articles/sample_ramp_new_fits/12462491>`_.
There is a minimal pytest script that is in 'iris_pipeline/tests'. THis also requires the 'sample_ramp_new.fits' from the link above.

The sampling.cfg gives the configurations for the pipeline

``sampling.cfg``:

.. code-block:: ini

name = "rop"
class = "iris_pipeline.pipeline.ROPPipeline"
save_results = True

    [steps]
      [[nonlincorr]]
      [[readoutsamp]]
       mode='mcds'
        

The sampling mode is set by the ``mode`` keyword which can be ``mcds`` or ``utr``. MCDS algorithm also requires the group number, the number of reads to be co-added. This is currently hardcoded in this version.


Execute the pipeline from the command line
------------------------------------------

We can use ``tmtrun`` from a terminal to execute the pipeline:

::

   tmt sampling.cfg sample_ramp.fits

here is the output log:

.. code:: bash

		2020-06-09 19:46:04,763 - stpipe.rop - INFO - ROPPipeline instance created.
		2020-06-09 19:46:04,764 - stpipe.rop.nonlincorr - INFO - NonlincorrStep instance created.
		2020-06-09 19:46:04,765 - stpipe.rop.readoutsamp - INFO - ReadoutsampStep instance created.
		2020-06-09 19:46:04,801 - stpipe.rop - INFO - Step rop running with args ('sample_ramp_new.fits',).
		2020-06-09 19:46:05,405 - stpipe.rop - INFO - Prefetching reference files for dataset: 'sample_ramp_new.fits' reftypes = ['nonlincoeff']
		2020-06-09 19:46:07,018 - stpipe.rop - INFO - Prefetch for NONLINCOEFF reference file is '/home/arun/crds_cache/references/tmt/iris/tmt_iris_nonlin_coeff.fits'.
		2020-06-09 19:46:07,019 - stpipe.rop - INFO - Starting ROP Pipeline ...
		2020-06-09 19:46:07,144 - stpipe.rop.nonlincorr - INFO - Step nonlincorr running with args (<TMTRampModel(1, 4, 10, 10) from sample_ramp_new.fits>,).
		2020-06-09 19:46:07,283 - stpipe.rop.nonlincorr - INFO - Step nonlincorr done
		2020-06-09 19:46:07,321 - stpipe.rop.readoutsamp - INFO - Step readoutsamp running with args (<TMTRampModel(1, 4, 10, 10) from sample_ramp_new.fits>,).
		2020-06-09 19:46:07,343 - stpipe.rop.readoutsamp - INFO - MCDS Sampling Selected
		(10, 10)
		2020-06-09 19:46:07,410 - stpipe.rop.readoutsamp - INFO - Step readoutsamp done
		2020-06-09 19:46:07,528 - stpipe.rop - INFO - Saved model in sample_ramp_new_rop.fits
		2020-06-09 19:46:07,529 - stpipe.rop - INFO - Step rop done



This creates a sample_ramp_new_rop.fits file in the working directory that is the processed 
