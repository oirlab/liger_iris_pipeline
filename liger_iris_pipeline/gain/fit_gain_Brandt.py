#!/usr/bin/env python

# Author: Tim Brandt
# Shared with HISPEC and Liger teams in Aug 2025
#
# Reference:
# Brandt, T. D., "Computing the Electronic Gain for Detectors Read Out Up-the-ramp", PASP, 137, 125006 (2025)
# https://ui.adsabs.harvard.edu/abs/2025PASP..137l5006B/abstract

import numpy as np
from ..ramp_fitting import fitramp_Brandt as fitramp
from ..ramp_fitting import fitramp_cython_Brandt as fitramp_cython

import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'


def gen_likelihood_map(diffs_lin, diffs_quad, covar, sigs, gains, alphas,
                       countratesidentical=False, asig=0,
                       cguess=None, d2use=None,readtime=None):
    
    """
    Generate a 3D array of the log likelihood of the ramp fit
    marginalized over the count rates ramp-by-ramp (or, if the
    countratesidentical variable is set to True, assume that all ramps
    have the same count rate).  Returns a 3D array of the size of
    len(sigs) x len(gains) x len(alphas), where sig is the read noise,
    gain is the gain in electrons/DN, and alpha is the nonlinearity
    coefficient.  Chi squared is equal to this returned array times
    -2.

    Parameters
    ----------
    diffs_lin : 2D array of floats
        Size nreads-1 x nramps. Differences between consecutive reads.
    diffs_quad : 2D array of floats
        Size nreads-1 x nramps. Differences between the squares of the values (from a designated pedestal) in consecutive reads
    covar : fitramp.Covar class
        Should be appropriate for diffs_lin
    sigs : list of floats
        Trial read noise values
    gains : list of floats
        Trial gain values
    alphas : list of floats
        Trial nonlinearity coefficient values
    asig : float, optional
        Standard deviation of the read noise from other constraints. If the best-fit read noise from this other constraint is sigs[1], asig will incorporate this constraint to the likelihood.
    countratesidentical : boolean, optional
        Assume that the count rate is the same for all ramps? Default False.
    cguess : 1D array of floats or None, optional
        Count rates for the purposes of computing a covariance matrix. Default None. If None, compute cguess from the nonlinearity-corrected ramps.
    d2use : 2D array of bools or None, optional
        Boolean mask of differences between reads to use for computing a likelihood. If None, use all read differences.

    Returns
    -------
    logL : 3D array of floats
        log likelihood, shape (len(sigs), len(gains), len(alphas))

    """

    nsig = len(sigs)
    ngain = len(gains)
    nalph = len(alphas)
    
    logL = np.zeros((nsig, ngain, nalph))

    # Normally, the lines below will not be used; these arrays
    # should be supplied as input to the routine.
    
    n0, n1 = diffs_lin.shape
    if d2use is None:
        diffs2use = np.ones((n0, n1), dtype=np.uint8)
    else:
        diffs2use = d2use

    # Estimate the covariance matrix inside this routine?  This will
    # be done using the linearity-corrected ramps.
    
    if cguess is None:
        dynamic_cguess = True
    else:
        dynamic_cguess = False
        
    for k in range(nalph):
        
        diffs_nonlinscaled = diffs_lin + alphas[k]*diffs_quad

        if dynamic_cguess:
            cguess = np.sum(diffs_nonlinscaled*diffs2use, axis=0)
            cguess /= np.sum(diffs2use, axis=0)
            cguess *= cguess > 0
        
        for j in range(ngain):   
                
            for i in range(nsig): 
                r = fitramp_cython.fit_ramps(
                    diffs_nonlinscaled, diffs2use,
                    covar.alpha_phnoise/gains[j], covar.beta_phnoise/gains[j],
                    covar.alpha_readnoise, covar.beta_readnoise,
                    sigs[i], cguess, n1, n0)
                
                logdetC, A, B, C, countrate, chisq, uncert = r

                # Can only use the lines below if we are *sure* that the count
                # rates are all the same.

                if countratesidentical:
                    c = np.sum(countrate*C)/np.sum(C)
                    chisqval = A - 2*c*B + c**2*C
                    logsigval = -0.5*np.log(np.sum(C))
                else:
                    chisqval = chisq
                    logsigval = fitramp_cython.logsum(uncert, n1)

                logL[i, j, k] = np.sum(-chisqval/2 - 0.5*logdetC) + logsigval

                # Incorporate other information about the read noise.
                if asig != 0:
                    if i == 0 or i == 2:
                        logL[i, j, k] += asig

    return logL


def fitquad(diffs_lin, diffs_quad, covar, sigs, gains, alphas=[0], asig=0,
              countratesidentical=False, cguess=None, d2use=None, log=True):

    """
    Fit a quadratic form to the probability distributions from
    marginalizing the ramps over the count rates.  This function
    will return the vertex of the fit, the covariance matrix
    implied by the coefficients, and the coefficients themselves.
    
    Parameters
    ----------
    diffs_lin : 2D array of float
        Size (nreads-1, nramps). Differences between consecutive reads.
    diffs_quad : 2D array of float
        Size (nreads-1, nramps). Differences between the squares of the values 
        (from a designated pedestal) in consecutive reads.
    covar : fitramp.Covar
        Should be appropriate for diffs_lin.
    sigs : list of float
        Trial read noise values.
    gains : list of float
        Trial gain values.
    alphas : list of float
        Trial nonlinearity coefficient values.
    asig : float, optional
        Standard deviation of the read noise from other constraints. If the best-fit read noise
        from this other constraint is sigs[1], asig will incorporate this constraint into the likelihood.
    countratesidentical : bool, optional
        Assume that the count rate is the same for all ramps. Default is False.
    cguess : 1D array of float or None, optional
        Count rates for computing a covariance matrix. Default is None. If None, compute cguess
        from the nonlinearity-corrected ramps.
    d2use : 2D array of bool or None, optional
        Boolean mask of differences between reads to use for computing a likelihood. If None,
        use all read differences.
    log : bool, optional
        Use logarithmic coordinates for the quadratic form. Default is True.

    Returns
    -------
    center : tuple of float
        Center of the quadratic form in gain, read noise, nonlinearity. The coordinates
        are given in log(gain) and log(readnoise) if log is True.
    cov : 2D array of float
        Covariance matrix of the log likelihood as estimated by the quadratic form fit.
    c_2d : list of float
        Coefficients describing the quadratic form.


    """
    
    logL = gen_likelihood_map(diffs_lin, diffs_quad, covar,
                              sigs, gains, alphas, asig=asig,
                              countratesidentical=countratesidentical,
                              cguess=cguess, d2use=d2use)

    arr = np.ones((len(sigs)*len(gains)*len(alphas), 10))
    if log:
        x, y, z = np.meshgrid(np.log(gains), np.log(sigs), alphas)
    else:        
        x, y, z = np.meshgrid(gains, sigs, alphas)
    x = x.flatten()
    y = y.flatten()
    z = z.flatten()
    arr[:, 1] = x
    arr[:, 2] = y
    arr[:, 3] = z
    arr[:, 4] = x*y
    arr[:, 5] = x*z
    arr[:, 6] = y*z    
    arr[:, 7] = x**2
    arr[:, 8] = y**2
    arr[:, 9] = z**2
    
    c = np.linalg.lstsq(arr, logL.flatten(), rcond=None)[0]

    # the covariance matrix interpreting the quadratic form as a log likelihood
    
    Cinv = -np.array([[2*c[7], c[4], c[5]],
                      [c[4], 2*c[8], c[6]],
                      [c[5], c[6], 2*c[9]]])

    # We might be fitting a quadratic form in 3d; we might be fitting one
    # in 2d.
    
    if len(alphas) > 1:
        cov = np.linalg.inv(Cinv)
    
        # the vertex of the quadratic form
        xc, yc, zc = np.linalg.solve(Cinv, np.array([c[1], c[2], c[3]]))

        return (xc, yc, zc), cov, c

    else:
        cov = np.linalg.inv(Cinv[:2, :2])
    
        # the vertex of the quadratic form
        xc, yc = np.linalg.solve(Cinv[:2, :2], np.array([c[1], c[2]]))
        c_2d = np.array([c[0], c[1], c[2], c[4], c[7], c[8]])
        
        return (xc, yc), cov, c_2d


def get_best_nonlinearity(diffs_lin, diffs_quad, covar, sigs, gains,
                           alpha_offset, dalpha, asig, cguess=None, d2use=None):

    """
    
    Fit a quadratic form for three values of the nonlinearity
    coefficient, and then use a parzabolic fit to find the highest gain
    and the nonlinearity coefficient corresponding to this highest
    gain.

    Parameters
    ----------
    diffs_lin : 2D array of float
        Size (nreads-1, nramps). Differences between consecutive reads.
    diffs_quad : 2D array of float
        Size (nreads-1, nramps). Differences between the squares of the values 
        (from a designated pedestal) in consecutive reads.
    covar : fitramp.Covar
        Should be appropriate for diffs_lin.
    sigs : list of float
        Trial read noise values.
    gains : list of float
        Trial gain values.
    alpha_offset : float
        Trial nonlinearity coefficient value.
    dalpha : float
        Offset in nonlinearity coefficient to try to fit a parabola to maximize the gain.
    asig : float, optional
        Standard deviation of the read noise from other constraints. If the best-fit read noise
        from this other constraint is sigs[1], asig will incorporate this constraint into the likelihood.
    cguess : 1D array of float or None, optional
        Count rates for computing a covariance matrix. Default is None. If None, compute cguess
        from the nonlinearity-corrected ramps.
    d2use : 2D array of bool or None, optional
        Boolean mask of differences between reads to use for computing a likelihood. If None,
        use all read differences.

    Returns
    -------
    bestloggain : float
        Best-fit log gain.
    alphabest : float
        Best nonlinearity coefficient (the one that yields the highest best-fit gain).
    alpha_inc : float
        Offset between alphabest and the input alpha_offset. Can be used to assess convergence.
    """
    
    alphalist = [alpha_offset + i*dalpha for i in [-1, 0, 1]]

    xclist = []
    for alpha in alphalist:
        (xc, yc), cov, _ = fitquad(
            diffs_lin, diffs_quad, covar, sigs, gains,
            alphas=[alpha], asig=asig, cguess=cguess, d2use=d2use)
        xclist += [xc*1.]
                
    a = 0.5*(xclist[2] + xclist[0] - 2*xclist[1])
    b = 0.5*(xclist[2] - xclist[0])
    c = xclist[1]
    
    alphabest = alphalist[1] - dalpha*b/(2*a)
    alpha_inc = -dalpha*b/(2*a)
    bestloggain = c - b**2/(4*a)

    return bestloggain, alphabest, alpha_inc


def fit_gain_linearity(ramps_dark, ramps_illum, fit_nonlin=True,
                       alpha_offset=2e-6, dalpha=2e-6, dalpha2=5e-7,
                       gainguess=1.85, maxiter_nonlin=10, snrscalefac=1):

    """
    Main function: fit gain, read noise, nonlinearity.

    Parameters
    ----------
    diffs_lin : 2D array of floats
        Size nreads-1 x nramps. Differences between consecutive reads.
    diffs_quad : 2D array of floats
        Size nreads-1 x nramps. Differences between the squares of the values (from a designated pedestal) in consecutive reads
    covar : fitramp.Covar class
        Should be appropriate for diffs_lin
    sigs : list of floats
        Trial read noise values
    gains : list of floats
        Trial gain values
    alphas : list of floats
        Trial nonlinearity coefficient values
    asig : float, optional
        Standard deviation of the read noise from other constraints. If the best-fit read noise from this other constraint is sigs[1], asig will incorporate this constraint to the likelihood.
    countratesidentical : boolean, optional
        Assume that the count rate is the same for all ramps? Default False.
    cguess : 1D array of floats or None, optional
        Count rates for the purposes of computing a covariance matrix. Default None. If None, compute cguess from the nonlinearity-corrected ramps.
    d2use : 2D array of bools or None, optional
        Boolean mask of differences between reads to use for computing a likelihood. If None, use all read differences.
    log : bool, optional
        Use logarithmic coordinates for the quadratic form? Default True.

    Returns
    -------
    center : tuple of two or three floats
        Center of the quadratic form in gain, read noise, nonlinearity. The coordinates will be given in log(gain) and log(readnoise) if the argument log is True.
    cov : 2D array of floats
        The covariance matrix of the log likelihood as estimated by the quadratic form fit
    c_2d : list of floats
        The coefficients describing the quadratic form
    
    """
    
    Nres = ramps_dark.shape[0]
    Nramps = ramps_dark.shape[1] + ramps_illum.shape[1]

    readtimes_dark = np.arange(ramps_dark.shape[0]) + 1
    readtimes_illum = np.arange(ramps_illum.shape[0]) + 1
    covar_dark = fitramp.Covar(readtimes_dark)
    covar_illum = fitramp.Covar(readtimes_illum)

    # Anchor the nonlinearity correction to the average pixel value
    # of the dark ramps.
    
    y0 = np.median(ramps_dark)

    darkdiffs_lin = np.diff(ramps_dark, axis=0)
    darkdiffs_quad = np.diff((ramps_dark - y0)**2, axis=0)
    
    # Initial estimate of the read noise
    sig_rn = np.median(np.std(darkdiffs_lin/np.sqrt(2), axis=0, ddof=1))
    d2u_dark = np.abs(darkdiffs_lin) < 6*sig_rn
    d2u_dark = d2u_dark.astype(np.uint8)

    # Should raise a ValueError here.
    if sig_rn == 0:
        raise ValueError("Zero dispersion in dark ramps implies no read noise.")
    
    # This parameter controls the spacing of the samples when fitting
    # a quadratic form.
    snrscale = snrscalefac*np.sqrt(75/(Nramps*Nres))
    
    # Run this twice to get the best read noise: first with a larger
    # interval, then with a smaller interval around the best value
    # from the first iteration.

    cen = 0
    for fac in [1, 0.2]:
        
        sigs = sig_rn*np.exp((np.arange(-1, 2)*fac + cen)*snrscale)
        
        # Unit gain, zero nonlinearity for the darks.
        gains = [1]
        alphas = [0]
        logL = gen_likelihood_map(darkdiffs_lin, darkdiffs_quad,
                                  covar_dark, sigs, gains, alphas,
                                  d2use=d2u_dark)
        logL = logL.flatten()
        
        b = 0.5*(logL[2] - logL[0])
        
        # asig will combine the likelihood from the read noise derived
        # from the dark frames with the likelihood derived from the
        # illuminated frames.
        asig = 0.5*(logL[2] + logL[0] - 2*logL[1])
        
        # Displacement (in units of dsig) of the new best-fit read noise
        cen = -b/(2*asig)
        
    # The rest of the calculations will use this array of read noise
    # values.  The central value is the best-fit read noise from the
    # darks.
    sigs *= np.exp(cen*fac*snrscale)
    
    gains = gainguess*np.exp(np.arange(-1, 2)*snrscale)
    
    illumdiffs_lin = np.diff(ramps_illum, axis=0)
    illumdiffs_quad = np.diff((ramps_illum - y0)**2, axis=0)
    
    # Mask illum read differences with more than 10sigma discrepancies
    # The 10 sigma threshold accounts for a poorly estimated gain,
    # where the actual gain is significantly lower than estimated.
    # Need to estimate count rates first.
    
    ctrates = np.median(illumdiffs_lin, axis=0)
    ctrates *= ctrates > 0
    totalnoise = np.sqrt(sig_rn**2 + ctrates/gainguess)
    d2u_illum = np.abs(illumdiffs_lin - ctrates) < 10*totalnoise
    d2u_illum = d2u_illum.astype(np.uint8)
    
    # If we are not fitting for any nonlinearity, we can take a shortcut.
    
    if not fit_nonlin:
        (xc, yc), cov, _ = fitquad(
            illumdiffs_lin, illumdiffs_quad, covar_illum, sigs, gains,
            d2use=d2u_illum)
        return xc, yc, 0, cov

    # If we are fitting for nonlinearity, we have a bit more work to do.
    
    xcbest, alphabest, alpha_inc = get_best_nonlinearity(
        illumdiffs_lin, illumdiffs_quad, covar_illum, sigs, gains,
        alpha_offset, dalpha, asig, d2use=d2u_illum)

    # Update the array of trial gains.  The 0.6 is hardcoded below--
    # perhaps make this tunable by the user?
    
    gains = np.exp(np.arange(-1, 2)*snrscale + xcbest)

    # Iterate to find the nonlinearity correction that gives
    # the highest best-fit gain.
    
    nonlin_ok = False
    for k in range(maxiter_nonlin):
        
        xcbest, alphabest, alpha_inc = get_best_nonlinearity(
            illumdiffs_lin, illumdiffs_quad, covar_illum, sigs, gains,
            alphabest, dalpha2, asig, d2use=d2u_illum)
        
        # Continue for maxiter_nonlin iterations, or until our
        # new best-fit value is within the searched interval.
        
        if np.abs(alpha_inc/dalpha2) < 1:
            nonlin_ok = True
            break

    # Update the array of trial gains one more time.
    
    gains = np.exp(np.arange(-1, 2)*0.6*snrscale + xcbest)

    # One last quadratic form fit at the best nonlinearity correction
    (xc, yc), cov, _ = fitquad(
        illumdiffs_lin, illumdiffs_quad, covar_illum, sigs, gains,
        alphas=[alphabest], asig=asig, d2use=d2u_illum)
    
    # Apply a very small statistical correction to the gain
    xc -= np.sqrt(1/(Nramps*(Nres - 1)))
    zc = alphabest
    
    # Unconverged nonlinearity
    if not nonlin_ok:
        raise RuntimeWarning("Nonlinearity calculation did not converge.")
    if cov[0, 0] <= 0:
        raise RuntimeWarning("Invalid derived covariance for gain, nonlinearity.")

    return xc, yc, zc, cov