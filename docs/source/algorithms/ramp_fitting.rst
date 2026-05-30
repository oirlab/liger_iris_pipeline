============
Ramp Fitting
============

There are five methods for sampling / fitting the up the ramp (UTR) data.

1. **cds**: Correlated double sampling using the last non-saturated read and the second read (to avoid kTC noise). If only two reads are available, the first read is used.

2. **mcds**: Multi correlated double sampling. Same as CDS, but uses the average of multiple reads at the beginning and end of the ramp to reduce readnoise. The number of reads to coadd is set by the argument ``mcds_num_coadd``.

3. **ols**: Ordinary least squares. This method fits a straight line to the ramp data using the ordinary least squares approach. This method is simple and computationally efficient but is not optimal with significant photon noise.

4. **jwst_fixsen**: This method assumes that the covariance is piece-wise constant by dividing 9 different regimes of various ratios of readnoise and photon noise. This is referenced as OLS in the JWST pipeline. Fixsen+2000 https://ui.adsabs.harvard.edu/abs/2000PASP..112.1350F/abstract

5. **jwst_likely**: Uses the maximum-likelihood from Brandt (2024) to fit the ramps, which is the optimal approach (but assuming constant illumination). Reference: Brandt, T. D., PASP, 136, 045005 (2024) https://ui.adsabs.harvard.edu/abs/2024PASP..136d5005B/abstract

6. **cython_likely**: Same as jwst_likely, but implemented in Cython for better performance (author: Brandt, Tim).


*More to come as DRP is developed*


Documentation
-------------

.. autoclass:: liger_iris_pipeline.ramp_fitting.fit_ramp_step.RampFitStep
   :members:
   :undoc-members:
   :no-index: