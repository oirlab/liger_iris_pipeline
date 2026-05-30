
# Author: Tim Brandt
# Shared with HISPEC team in Aug 2025
# Modified by JB Ruffio on 2026-01-01 to fix compatibility with newer numpy versions.
#
# Reference:
# Brandt, T. D., "A Classic Nonlinearity Correction Algorithm for Detectors Read Out Up-the-ramp", PASP, 137, 125005 (2025)
# https://ui.adsabs.harvard.edu/abs/2025PASP..137l5005B/abstract

import numpy as np
from scipy import special
import warnings
from numpy.polynomial import legendre, Polynomial


class Covar:

    """

    class Covar holding read and photon noise components of alpha and
    beta and the time intervals between the resultant midpoints

    """
    
    def __init__(self, read_times, singlereads=False):

        """

        Compute alpha and beta, the diagonal and off-diagonal elements of
        the covariance matrix of the resultant differences, and the time 
        intervals between the resultant midpoints.

        Parameters
        ----------
        1. read_times [list of values or lists for the times of reads.  If 
                      a list of lists, times for reads that are averaged
                      together to produce a resultant.]
        """

        if not singlereads:
            mean_t = []   # mean time of the resultant as defined in the paper
            tau = []   # variance-weighted mean time of the resultant
            N = []  # Number of reads per resultant
            
            for times in read_times:
                mean_t += [np.mean(times)]
                
                if hasattr(times, "__len__"):
                    N += [len(times)]
                    k = np.arange(1, N[-1] + 1)
                    tau += [1/N[-1]**2*np.sum((2*N[-1] + 1 - 2*k)*np.array(times))]
                else:
                    tau += [times]
                    N += [1]
            
            mean_t = np.array(mean_t)
            tau = np.array(tau)
            N = np.array(N)
        else:
            mean_t = read_times
            tau = read_times
            N = np.ones(read_times.shape)
        
        delta_t = mean_t[1:] - mean_t[:-1]

        self.delta_t = delta_t
        self.mean_t = mean_t
        self.tau = tau
        self.Nreads = N
        
        self.alpha_readnoise = (1/N[:-1] + 1/N[1:])/delta_t**2
        self.beta_readnoise = -1/N[1:-1]/(delta_t[1:]*delta_t[:-1])
        
        self.alpha_phnoise = (tau[:-1] + tau[1:] - 2*mean_t[:-1])/delta_t**2
        self.beta_phnoise = (mean_t[1:-1] - tau[1:-1])/(delta_t[1:]*delta_t[:-1])
                
class Nonlin_Result:

    def __init__(self):
        self.order = None
        self.slopes = None
        self.chisq = None
        self.nonlin_coefs = None
        self.superbias = None
        self.log_cond = None
        self.satval = None
        self.cov = None
        self.norm = None
        
        
def calc_A_matrix(diffs, diffs_pow, Cov, sig, gain, countrateguess=None,
                  diffs2use=None, rescale=True, dn_scale=10):

    """
    Calculate the matrix elements needed to compute a nonlinearity correction 

    Parameters
    ----------
    diffs : ndarray, shape (ndiffs, npix)
        Resultant differences.
    diff_pow : ndarray, shape (order+1, ndiffs, npix)
        Templates for nonlinearity fit.
    Cov : Covar
        Class holding the covariance matrix information.
    sig : ndarray, shape (npix,)
        Read noise.
    gain : ndarray, shape (npix,)
        Gain.
    countrateguess : ndarray, shape (npix,), default None
        Count rates to be used to estimate the covariance matrix. 
        If None, the average difference is used, replacing negative means with zeros.
    diffs2use : ndarray of bool, shape (ndiffs, npix), default None
        Boolean mask of whether to use each resultant difference for each pixel.
    rescale : bool, default True
        Scale the covariance matrix internally to avoid possible overflow/underflow 
        problems for long ramps. Slightly increases computational cost.
    dn_scale : int
        How often to keep tallies of the scale factor.


    Returns
    -------
    A_all : ndarray, shape (order, order)
        order is the first dimension of diffs_pow

    """

    if diffs2use is None:
        diffs2use = np.ones(diffs.shape, np.uint8)
    
    if countrateguess is None:
        # initial guess for count rate is the average of the unmasked
        # resultant differences unless otherwise specified.
        countrateguess = np.sum((diffs*diffs2use), axis=0)/np.sum(diffs2use, axis=0)
        countrateguess *= countrateguess > 0

    # Elements of the covariance matrix

    if len(Cov.alpha_phnoise.shape) == 1:

        alpha_phnoise = (countrateguess/gain)*Cov.alpha_phnoise[:, np.newaxis]
        alpha_readnoise = sig**2*Cov.alpha_readnoise[:, np.newaxis]
        alpha = alpha_phnoise + alpha_readnoise

        beta_phnoise = (countrateguess/gain)*Cov.beta_phnoise[:, np.newaxis]
        beta_readnoise = sig**2*Cov.beta_readnoise[:, np.newaxis]
        beta = beta_phnoise + beta_readnoise

    else:

        alpha_phnoise = countrateguess*Cov.alpha_phnoise
        alpha_readnoise = sig**2*Cov.alpha_readnoise
        alpha = alpha_phnoise + alpha_readnoise

        beta_phnoise = countrateguess*Cov.beta_phnoise
        beta_readnoise = sig**2*Cov.beta_readnoise
        beta = beta_phnoise + beta_readnoise
        
    # Mask resultant differences that should be ignored.  This is half
    # of what we need to do to mask these resultant differences; the
    # rest comes later.

    d = diffs*diffs2use

    d_pow = diffs_pow*diffs2use[np.newaxis, :]
    order = diffs_pow.shape[0] - 1
        
    beta = beta*diffs2use[1:]*diffs2use[:-1]

    ndiffs, npix = alpha.shape
        
    # Rescale the covariance matrix to a determinant of 1 to
    # avoid possible overflow/underflow.  The uncertainty and chi
    # squared value will need to be scaled back later.  Note that
    # theta[-1] is the determinant of the covariance matrix.
    #
    # The method below uses the fact that if all alpha and beta
    # are multiplied by f, theta[i] is multiplied by f**i.  Keep
    # a running track of these factors to construct the scale at
    # the end, and keep scaling throughout so that we never risk
    # overflow or underflow.
    
    if rescale:
        theta = np.ones((ndiffs + 1, npix))
        theta[1] = alpha[0]
        
        scale = theta[0]*1
        for i in range(2, ndiffs + 1):
        
            theta[i] = alpha[i - 1]/scale*theta[i - 1] - beta[i - 2]**2/scale**2*theta[i - 2]

            # Scaling every ten steps is safe for alpha up to 1e20 
            # or so and incurs a negligible computational cost for 
            # the fractional power.
            
            if i % int(dn_scale) == 0 or i == ndiffs:
                f = theta[i]**(1/i)
                scale *= f
                theta[i - 1] /= theta[i]/f
                theta[i - 2] /= theta[i]/f**2
                theta[i] = 1 
    else:
        scale = 1
            
    alpha /= scale
    beta /= scale
    
    # All definitions and formulas here are in the paper.

    theta = np.ones((ndiffs + 1, npix))
    theta[1] = alpha[0]
    for i in range(2, ndiffs + 1):
        theta[i] = alpha[i - 1]*theta[i - 1] - beta[i - 2]**2*theta[i - 2]
        
    phi = np.ones((ndiffs + 1, npix))
    phi[ndiffs - 1] = alpha[ndiffs - 1]
    for i in range(ndiffs - 2, -1, -1):
        phi[i] = alpha[i]*phi[i + 1] - beta[i]**2*phi[i + 2]

    sgn = np.ones((ndiffs, npix))
    sgn[::2] = -1

    ThetaD_all = np.zeros((order + 1, ndiffs + 1, npix))
    ThetaD_all[:, 1] = -d_pow[:, 0]*theta[0]
    for i in range(1, ndiffs):
        ThetaD_all[:, i + 1] = beta[i - 1]*ThetaD_all[:, i] + sgn[i]*d_pow[:, i]*theta[i]

    PhiD_all = np.zeros((order + 1, ndiffs, npix))
    for i in range(ndiffs - 2, -1, -1):
        PhiD_all[:, i] = (PhiD_all[:, i + 1] + sgn[i + 1]*d_pow[:, i + 1]*phi[i + 2])*beta[i]
        

    A_all = np.zeros((order + 1, order + 1, d.shape[1]))
    for i in range(order + 1):

        dB = sgn/theta[ndiffs]*(phi[1:]*ThetaD_all[i, 1:] +
                                theta[:-1]*PhiD_all[i])
        
        for j in range(i, order + 1):

            A_all[i, j] = np.sum(dB*d_pow[j], axis=0)
            
            # Matrix is symmetric
            A_all[j, i] = A_all[i, j]
            
    return A_all/scale


def get_nonlin_coefs(data_list, sig, gain, order, intercepts, nsamples_est=5,
                     d2u_list=None, satval=6e4, use_legendre=True,
                     calc_cond=False, last_pars=None, rescale_domain=True):
    
    """
    Use many ramps to fit for nonlinearity correction coefficients
    
    Parameters
    ----------
    data_list : list of ndarrays
        list of 2D ndarrays for ramps, each of shape (nreads, npixels)
    sig : ndarray
        1D array for read noise, shape (npixels)
    gain : ndarray
        1D array for read noise, shape (npixels)
    order : int
        order of polynomial to fit for the nonlinearity correction
    intercepts :  ndarray
        bias levels to anchor nonlinearity fit, shape (npixels)
    nsamples_est : int, default 5
        number of initial samples whose median provides an estimate of
        the count rate for the total slope target and for getting a
        baseline to reject egregious jumps.  
    d2u_list : list of ndarrays or None, default None
        list of uint8 ndarrays, same length/shapes as data_list, =1 for
        the read differences that we should use.  If None, use all
        reads. Arrays will be further flagged in this routine for
        saturation and for egregious jumps
    satval : float or ndarray, default 6e4
        saturation value.  If an ndarray, should be of shape (npixels)
    use_legendre : boolean, default True
        fit in the Legendre polynomial basis?
    calc_cond : boolean, default False
        compute the condition number of the matrix for each pixel?
    last_pars : Nonlin_Result or None, default None
        output of a previous run of get_nonlin_coefs to set the
         covariance matrix from the previously estimated count rates
    rescale_domain : boolean, default True
        rescale the domain to [-1, 1] for better numerical behavior?
    
    Returns
    -------
    Nonlin_Result
        result structure with lots of information
    
    """
    nramps = len(data_list)
    N = nramps - 1
    npixels = data_list[0].shape[-1]
    A = np.zeros((order + N, order + N, npixels))
    Btot = np.zeros((npixels))

    # Re-map the domain to [-1, 1]
    if rescale_domain:
        offset = (satval - intercepts)/2
        norm = offset
    else:
        offset = 0*intercepts
        norm = np.amax(np.array([data_list[i][-1] for i in range(len(data_list))]), axis=0) - intercepts
    xi = None
    
    for i in range(nramps):
        nreads = len(data_list[i])
        C = Covar(np.arange(1, nreads + 1), singlereads=True)
        
        resid = data_list[i]*1. - intercepts - offset
        diff = (resid[1:] - resid[:-1])/C.delta_t[:, np.newaxis]
        
        # Try to flag and remove really obvious jumps.

        med_diff = np.median(diff[:nsamples_est], axis=0)
        diff_ok = diff < 2*np.abs(med_diff[np.newaxis, :]) + 5*sig
        d2u = (data_list[i][1:] < satval) & (diff_ok)
        
        d_pow = np.ones((order + 1, diff.shape[0], diff.shape[1]))

        # Standard polynomial basis set
        if not use_legendre:
            resid_pow = resid/norm
            for j in range(1, order + 1):
                d_pow[j] = (resid_pow[1:] - resid_pow[:-1])/C.delta_t[:, np.newaxis]
                resid_pow *= resid/norm

        # Legendre polynomial basis set
        else:
            for j in range(1, order + 1):
                legcoef = [0]*j + [1]
                resid_pow_leg = legendre.legval(resid/norm, legcoef)
                d_pow[j] = resid_pow_leg[1:] - resid_pow_leg[:-1]

        # Compute the necessary matrix elements.
        if last_pars is not None:
            cguess = last_pars.slopes[:, i]
            cguess *= cguess > 0
        else:
            cguess = None

        A_all = calc_A_matrix(diff, d_pow, C, sig, gain, diffs2use=d2u,
                              countrateguess=cguess)

        Btot += np.median(diff[0:nsamples_est], axis=0)/norm

        # Embed this within the larger matrix.
        if i < N:
            A[N:, N:] += A_all[1:, 1:]
            A[N:, i] -= A_all[1:, 0]
            A[i, N:] -= A_all[0, 1:]
            A[i, i] += A_all[0, 0]
            
        # If this is the final ramp, need to substitute for b and
        # take care of all of the cross terms that are now nonzero
        else:            
            A[N:, N:] += A_all[1:, 1:]            
            A[N:, :N] += A_all[1:, 0][:, np.newaxis]
            A[:N, N:] += A_all[0, 1:][np.newaxis, :]
            A[:N, :N] += A_all[0, 0]

            xi = np.zeros((A.shape[0], A.shape[-1]))
            xi[:N] += Btot*A_all[0, 0]
            xi[N:] += Btot*A_all[1:, 0]

    result = Nonlin_Result()
    result.order = order
    result.superbias = intercepts
    result.satval = satval
    if calc_cond:
        result.log_cond = np.log10(np.linalg.cond(np.swapaxes(A, 0, 2)))

    # Solve for the slopes and nonlinearity coefficients.

    # JB Ruffio 1/1/2026 note: Old line that does not work with newer numpy versions
    # lstsq_coefs = np.linalg.solve(np.swapaxes(A, 0, 2), xi.T)

    # JB Ruffio 1/1/2026 Update: New code that seems to work. Based on Chatgpt, but I don't fully understand how np.linalg.solve manages dimensions.
    A_batched = np.moveaxis(A, 2, 0)  # (npixels, 302, 302)
    b = np.moveaxis(xi, 1, 0)[..., None]  # (npixels, 302, 1)
    x = np.linalg.solve(A_batched, b)  # (npixels, 302, 1)
    lstsq_coefs = x[..., 0]  # (npixels, 302)

    # Compute chi squared summed over the ramps.
    chisq = np.einsum('ij,jki,ik->i', lstsq_coefs, A, lstsq_coefs)
    chisq -= 2*np.einsum('ji,ij->i', xi, lstsq_coefs)
    chisq += Btot*xi[0]
    chisq *= norm**2
    
    result.chisq = chisq

    # Save the best-fit "true" slope of each ramp
    result.slopes = np.zeros((npixels, nramps))
    result.slopes[:, :-1] = lstsq_coefs[:, :N]*norm[:, np.newaxis]
    # Insert the m-th ramp's slope back in.    
    result.slopes[:, -1] = (Btot - np.sum(lstsq_coefs[:, :N], axis=1))*norm

    # Convert the polynomial coefficients to a standard form polynomial
    # with an origin at intercepts.
    
    result.nonlin_coefs = lstsq_coefs[:, N:]*1.
    # Constant term doesn't matter; insert a zero.
    polycoefs = np.zeros(order + 1)

    # Precompute factorials (gamma function).
    gamma_mp1 = [special.gamma(m + 1) for m in range(len(polycoefs))]
    
    for i in range(npixels):
        polycoefs[1:] = result.nonlin_coefs[i]
        if use_legendre:
            poly = Polynomial(legendre.leg2poly(polycoefs))
        else:
            poly = Polynomial(polycoefs)

        # Shift polynomial's origin back by offset
        newcoefs = [poly.deriv(m)(-(offset/norm)[i])/gamma_mp1[m]
                    for m in range(len(polycoefs))]
        result.nonlin_coefs[i] = np.array(newcoefs)[1:]

    # Convert units of coefficients back to DN to the appropriate power
    result.nonlin_coefs /= norm[:, np.newaxis]**np.arange(order)[np.newaxis, :]
    result.norm = norm[:, np.newaxis]**np.arange(order)[np.newaxis, :]
    result.cov = np.swapaxes(A, 0, 2)
    result.xi = xi
    
    return result
