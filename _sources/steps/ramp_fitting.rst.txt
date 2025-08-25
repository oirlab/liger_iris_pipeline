Ramp Fitting
============

Overview
--------

The step  determines the effective slope for a sequence of UTR reads. This is currently implemented with `numba <https://numba.readthedocs.io/en/stable/index.html#>`_.

**Class**: :py:class:`~liger_iris_pipeline.readout.fit_ramp_step.FitRampStep`


Algorithm
---------

Three methods are available for fitting the ramp:

**1. Correlated Double Sampling (CDS)** - The difference between the first (or probably second for most exposures) and last read are used to determine the slope.

**2. Multiple Correlated Double Sampling (MCDS)** - Similar to CDS, but multiple reads at the begining and end of the ramp are used to determine the slope.

**3. Ordinary least squares (OLS)** - The entire ramp is fit in a least squares framework. The current algorithm assumes reads are not correlated. Future algorithms will use a generalized least squares framework accounting for the covariance of each read.


Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.ramp.RampModel`
    The input file or ramp model to process.

**method** : ``str``
    Which method to use for ramp fitting. Options are 'CDS', 'MCDS', or 'OLS'. Default is 'OLS'.

**num_coadds** : ``int``
    Number of coadds to use for ramp fitting in MCDS mode. Default is 1 (equivalent to ``method='CDS'``).


Subarrays
---------

TBD

Calibration Files
-----------------

None.