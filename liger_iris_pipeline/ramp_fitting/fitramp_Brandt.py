# Author: Tim Brandt
# Shared with HISPEC team in Aug 2025
#
# Reference:
# Brandt, T. D., "Likelihood-based Jump Detection and Cosmic Ray Rejection for Detectors Read Out Up-the-ramp", PASP, 136, 045005 (2024)
# https://ui.adsabs.harvard.edu/abs/2024PASP..136d5005B/abstract
#
# Roman calibration pipeline reference:
# https://github.com/spacetelescope/romancal

import numpy as np
from scipy import special
import warnings

class Covar:

    """

    class Covar holding read and photon noise components of alpha and
    beta and the time intervals between the resultant midpoints

    """
    
    def __init__(self, read_times, pedestal=False):

        """

        Compute alpha and beta, the diagonal and off-diagonal elements of
        the covariance matrix of the resultant differences, and the time 
        intervals between the resultant midpoints.

        Parameters
        ----------
        readtimes : list of float or list of list of float
            Times of reads. If a list of lists, each sublist gives times for reads 
            that are averaged together to produce a resultant.
        pedestal : bool, default False
            Whether the covariance matrix includes terms for the first resultant. 
            Needed if fitting for the pedestal (i.e., the reset value).


        """
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
        
        delta_t = mean_t[1:] - mean_t[:-1]

        self.pedestal = pedestal
        self.delta_t = delta_t
        self.mean_t = mean_t
        self.tau = tau
        self.Nreads = N

        self.alpha_readnoise = (1/N[:-1] + 1/N[1:])/delta_t**2
        self.beta_readnoise = -1/N[1:-1]/(delta_t[1:]*delta_t[:-1])
        
        self.alpha_phnoise = (tau[:-1] + tau[1:] - 2*mean_t[:-1])/delta_t**2
        self.beta_phnoise = (mean_t[1:-1] - tau[1:-1])/(delta_t[1:]*delta_t[:-1])

        # If we want the reset value we need to include the first
        # resultant.  These are the components of the variance and
        # covariance for the first resultant.
        
        if pedestal:
            self.alpha_readnoise = np.array([1/N[0]/mean_t[0]**2]
                                            + list(self.alpha_readnoise))
            self.beta_readnoise = np.array([-1/N[0]/mean_t[0]/delta_t[0]]
                                           + list(self.beta_readnoise))
            self.alpha_phnoise = np.array([tau[0]/mean_t[0]**2]
                                          + list(self.alpha_phnoise))
            self.beta_phnoise = np.array([(mean_t[0] - tau[0])/mean_t[0]/delta_t[0]]
                                         + list(self.beta_phnoise))
            
    def calc_bias(self, countrates, sig, cvec, da=1e-7):

        """
        Calculate the bias in the best-fit count rate from estimating the
        covariance matrix.  This calculation is derived in the paper.

        Parameters
        ----------
        countrates : array_like
            Array of count rates at which the bias is desired.
        sig : float
            Single read noise.
        cvec : array_like
            Weight vector on resultant differences for initial estimation of count rate 
            for the covariance matrix. Will be renormalized inside this function.
        da : float, default 1e-7
            Fraction of the count rate plus sig**2 to use for finite difference estimate 
            of the derivative.

        Returns
        -------
        bias : array_like
            Bias of the best-fit count rate from using ``cvec`` plus the observed resultants 
            to estimate the covariance matrix.

        
        """
        
        if self.pedestal:
            raise ValueError("Cannot compute bias with a Covar class that includes a pedestal fit.")

        alpha = countrates[np.newaxis, :]*self.alpha_phnoise[:, np.newaxis]
        alpha += sig**2*self.alpha_readnoise[:, np.newaxis]
        beta = countrates[np.newaxis, :]*self.beta_phnoise[:, np.newaxis]
        beta += sig**2*self.beta_readnoise[:, np.newaxis]

        # we only want the weights; it doesn't matter what the count rates are.
        n = alpha.shape[0]
        z = np.zeros((len(cvec), len(countrates)))
        result_low_a = fit_ramps(z, self, sig, countrateguess=countrates)

        # try to avoid problems with roundoff error
        da_incr = da*(countrates[np.newaxis, :] + sig**2)
        
        dalpha = da_incr*self.alpha_phnoise[:, np.newaxis]
        dbeta = da_incr*self.beta_phnoise[:, np.newaxis]
        result_high_a = fit_ramps(z, self, sig, countrateguess=countrates+da_incr)
        # finite difference approximation to dw/da
        
        dw_da = (result_high_a.weights - result_low_a.weights)/da_incr

        bias = np.zeros(len(countrates))
        c = cvec/np.sum(cvec)
        
        for i in range(len(countrates)):

            C = np.zeros((n, n))
            for j in range(n):
                C[j, j] = alpha[j, i]
            for j in range(n - 1):
                C[j + 1, j] = C[j, j + 1] = beta[j, i]
                
            bias[i] = np.linalg.multi_dot([c[np.newaxis, :], C, dw_da[:, i]])

            sig_a = np.sqrt(np.linalg.multi_dot([c[np.newaxis, :], C, c[:, np.newaxis]]))
            bias[i] *= 0.5*(1 + special.erf(countrates[i]/sig_a/2**0.5))
            
        return bias
                

class Ramp_Result:
    
    def __init__(self):
        
        self.countrate = None
        self.chisq = None
        self.uncert = None
        self.var_poisson = None
        self.var_rdnoise = None
        self.weights = None
        self.pedestal = None
        self.uncert_pedestal = None
        self.covar_countrate_pedestal = None
        
        self.countrate_twoomit = None
        self.chisq_twoomit = None
        self.uncert_twoomit = None

        self.countrate_oneomit = None
        self.jumpval_oneomit = None
        self.jumpsig_oneomit = None
        self.chisq_oneomit = None
        self.uncert_oneomit = None

    def fill_masked_reads(self, diffs2use):

        """

        Replace countrates, uncertainties, and chi squared values that
        are NaN because resultant differences were doubly omitted.
        For these cases, revert to the corresponding values in with
        fewer omitted resultant differences to get the correct values
        without double-coundint omissions.

        Parameters
        ----------
        diffs2use : array_like
            A 2D array matching self.countrate_oneomit in 
            shape with zero for resultant differences that 
            were masked and one for differences that were 
            not masked.

        Notes
        -----
        This function replaces the relevant entries of
        self.countrate_twoomit, self.chisq_twoomit,
        self.uncert_twoomit, self.countrate_oneomit, and
        self.chisq_oneomit in place.  It does not return a value.

        """
        
        # replace entries that would be nan (from trying to
        # doubly exclude read differences) with the global fits.
            
        omit = diffs2use == 0
        ones = np.ones(diffs2use.shape)
            
        self.countrate_oneomit[omit] = (self.countrate*ones)[omit]
        self.chisq_oneomit[omit] = (self.chisq*ones)[omit]
        self.uncert_oneomit[omit] = (self.uncert*ones)[omit]

        omit = diffs2use[1:] == 0
        
        self.countrate_twoomit[omit] = (self.countrate_oneomit[:-1])[omit]
        self.chisq_twoomit[omit] = (self.chisq_oneomit[:-1])[omit]
        self.uncert_twoomit[omit] = (self.uncert_oneomit[:-1])[omit]
        
        omit = diffs2use[:-1] == 0
        
        self.countrate_twoomit[omit] = (self.countrate_oneomit[1:])[omit]
        self.chisq_twoomit[omit] = (self.chisq_oneomit[1:])[omit]
        self.uncert_twoomit[omit] = (self.uncert_oneomit[1:])[omit]
        
        
def fit_ramps(diffs, Cov, sig, countrateguess=None, diffs2use=None,
              detect_jumps=False, resetval=0, resetsig=np.inf, rescale=True,
              dn_scale=10):

    """
    Function fit_ramps.  Fits ramps to read differences using the 
    covariance matrix for the read differences as given by the diagonal
    elements and the off-diagonal elements.

    Parameters
    ----------
    diffs : array_like, shape (ndiffs, npix)
        Resultant differences.
    Cov : Covar
        Class holding the covariance matrix information.
    sig : array_like, shape (npix)
        Read noise.
    countrateguess : array_like, shape (npix), optional
        Count rates to be used to estimate the covariance matrix. Default is None.
    diffs2use : array_like, shape (ndiffs, npix), optional
        Boolean mask of whether to use each resultant difference for each pixel. Default is None.
    detect_jumps : bool, optional
        Run the jump detection machinery. Default is False.
    resetval : float or array_like, shape (npix), optional
        Priors on the reset values. Default is 0.
    resetsig : float or array_like, shape (npix), optional
        Uncertainties on the reset values. Default is np.inf.
    rescale : bool, optional
        Scale the covariance matrix internally. Default is True.

    Returns
    -------
    Ramp_Result
        Class holding detailed ramp information.


    """

    if diffs2use is None:
        diffs2use = np.ones(diffs.shape, np.uint8)
    
    if countrateguess is None:
        # initial guess for count rate is the average of the unmasked
        # resultant differences unless otherwise specified.
        if Cov.pedestal:
            countrateguess = np.sum((diffs*diffs2use)[1:], axis=0)/np.sum(diffs2use[1:], axis=0)
        else:
            countrateguess = np.sum((diffs*diffs2use), axis=0)/np.sum(diffs2use, axis=0)
        countrateguess *= countrateguess > 0

    # Elements of the covariance matrix

    if len(Cov.alpha_phnoise.shape) == 1:
        alpha_phnoise = countrateguess*Cov.alpha_phnoise[:, np.newaxis]
        alpha_readnoise = sig**2*Cov.alpha_readnoise[:, np.newaxis]
        alpha = alpha_phnoise + alpha_readnoise
        beta_phnoise = countrateguess*Cov.beta_phnoise[:, np.newaxis]
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
    beta = beta*diffs2use[1:]*diffs2use[:-1]
    #print(alpha.shape)
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

    #print(np.mean(theta[-1]), np.std(theta[-1]))
        
    phi = np.ones((ndiffs + 1, npix))
    phi[ndiffs - 1] = alpha[ndiffs - 1]
    for i in range(ndiffs - 2, -1, -1):
        phi[i] = alpha[i]*phi[i + 1] - beta[i]**2*phi[i + 2]

    sgn = np.ones((ndiffs, npix))
    sgn[::2] = -1

    Phi = np.zeros((ndiffs, npix))
    for i in range(ndiffs - 2, -1, -1):
        Phi[i] = Phi[i + 1]*beta[i] + sgn[i + 1]*beta[i]*phi[i + 2]
    
    # This one is defined later in the paper and is used for jump
    # detection and pedestal fitting.
    
    PhiD = np.zeros((ndiffs, npix))
    for i in range(ndiffs - 2, -1, -1):
        PhiD[i] = (PhiD[i + 1] + sgn[i + 1]*d[i + 1]*phi[i + 2])*beta[i]
        
    Theta = np.zeros((ndiffs, npix))
    Theta[0] = -theta[0]
    for i in range(1, ndiffs):
        Theta[i] = Theta[i - 1]*beta[i - 1] + sgn[i]*theta[i]
        
    ThetaD = np.zeros((ndiffs + 1, npix))
    ThetaD[1] = -d[0]*theta[0]
    for i in range(1, ndiffs):
        ThetaD[i + 1] = beta[i - 1]*ThetaD[i] + sgn[i]*d[i]*theta[i]
        
    beta_extended = np.ones((ndiffs, npix))
    beta_extended[1:] = beta
    
    # C' and B' in the paper
    
    dC = sgn/theta[ndiffs]*(phi[1:]*Theta + theta[:-1]*Phi)
    dC *= diffs2use

    dB = sgn/theta[ndiffs]*(phi[1:]*ThetaD[1:] + theta[:-1]*PhiD)

    # {\cal A}, {\cal B}, {\cal C} in the paper
    
    A = 2*np.sum(d*sgn/theta[-1]*beta_extended*phi[1:]*ThetaD[:-1], axis=0)
    A += np.sum(d**2*theta[:-1]*phi[1:]/theta[ndiffs], axis=0)
    
    B = np.sum(d*dC, axis=0)
    C = np.sum(dC, axis=0)

    r = Ramp_Result()

    # Finally, save the best-fit count rate, chi squared, uncertainty
    # in the count rate, and the weights used to combine the
    # resultants.

    if not Cov.pedestal:
        r.countrate = B/C
        r.chisq = (A - B**2/C)/scale
        r.uncert = np.sqrt(scale/C)
        r.weights = dC/C
        r.var_poisson = np.sum(r.weights**2*alpha_phnoise, axis=0)
        r.var_poisson += 2*np.sum(r.weights[1:]*r.weights[:-1]*beta_phnoise, axis=0)
        r.var_rdnoise = np.sum(r.weights**2*alpha_readnoise, axis=0)
        r.var_rdnoise += 2*np.sum(r.weights[1:]*r.weights[:-1]*beta_readnoise, axis=0)
    
    # If we are computing the pedestal, then we use the other formulas
    # in the paper.
        
    else:
        dt = Cov.mean_t[0]
        Cinv_11 = theta[0]*phi[1]/theta[ndiffs]
        
        # Calculate the pedestal and slope using the equations in the paper.
        # Do not compute weights for this case.

        b = dB[0]*C*dt - B*dC[0]*dt + dt**2*C*resetval/resetsig**2
        b /= C*Cinv_11 - dC[0]**2 + dt**2*C/resetsig**2
        a = B/C - b*dC[0]/C/dt
        r.pedestal = b
        r.countrate = a
        r.chisq = A + a**2*C + b**2/dt**2*Cinv_11
        r.chisq += - 2*b/dt*dB[0] - 2*a*B + 2*a*b/dt*dC[0]
        r.chisq /= scale
        
        # elements of the inverse covariance matrix
        M = [C, dC[0]/dt, Cinv_11/dt**2 + 1/resetsig**2]
        detM = M[0]*M[-1] - M[1]**2
        r.uncert = np.sqrt(scale*M[-1]/detM)
        r.uncert_pedestal = np.sqrt(scale*M[0]/detM)
        r.covar_countrate_pedestal = -scale*M[1]/detM
        
    # The code below computes the best chi squared, best-fit slope,
    # and its uncertainty leaving out each resultant difference in
    # turn.  There are ndiffs possible differences that can be
    # omitted.
    # 
    # Then do it omitting two consecutive reads.  There are ndiffs-1
    # possible pairs of adjacent reads that can be omitted.
    #
    # This approach would need to be modified if also fitting the
    # pedestal, so that condition currently triggers an error.  The
    # modifications would make the equations significantly more
    # complicated; the matrix equations to be solved by hand would be
    # larger.
    
    if detect_jumps:
        
        # The algorithms below do not work if we are computing the
        # pedestal here.

        if Cov.pedestal:
            raise ValueError("Cannot use jump detection algorithm when fitting pedestals.")

        # Diagonal elements of the inverse covariance matrix
    
        Cinv_diag = theta[:-1]*phi[1:]/theta[ndiffs]
        Cinv_diag *= diffs2use
        
        # Off-diagonal elements of the inverse covariance matrix
        # one spot above and below for the case of two adjacent
        # differences to be masked
        
        Cinv_offdiag = -beta*theta[:-2]*phi[2:]/theta[ndiffs]
        
        # Equations in the paper: best-fit a, b
        # 
        # Catch warnings in case there are masked resultant
        # differences, since these will be overwritten later.  No need
        # to warn about division by zero here.

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            a = (Cinv_diag*B - dB*dC)/(C*Cinv_diag - dC**2)
            b = (dB - a*dC)/Cinv_diag
        
            r.countrate_oneomit = a
            r.jumpval_oneomit = b
            
            # Use the best-fit a, b to get chi squared
            
            r.chisq_oneomit = A + a**2*C - 2*a*B + b**2*Cinv_diag - 2*b*dB + 2*a*b*dC
            # invert the covariance matrix of a, b to get the uncertainty on a
            r.uncert_oneomit = np.sqrt(Cinv_diag/(C*Cinv_diag - dC**2))
            r.jumpsig_oneomit = np.sqrt(C/(C*Cinv_diag - dC**2))

            r.chisq_oneomit /= scale
            r.uncert_oneomit *= np.sqrt(scale)
            r.jumpsig_oneomit *= np.sqrt(scale)
            
        # Now for two omissions in a row.  This is more work.  Again,
        # all equations are in the paper.  I first define three
        # factors that will be used more than once to save a bit of
        # computational effort.

        cpj_fac = dC[:-1]**2 - C*Cinv_diag[:-1]
        cjck_fac = dC[:-1]*dC[1:] - C*Cinv_offdiag
        bcpj_fac = B*dC[:-1] - dB[:-1]*C

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            # best-fit a, b, c
            c = (bcpj_fac/cpj_fac - (B*dC[1:] - dB[1:]*C)/cjck_fac)
            c /= cjck_fac/cpj_fac - (dC[1:]**2 - C*Cinv_diag[1:])/cjck_fac
            b = (bcpj_fac - c*cjck_fac)/cpj_fac
            a = (B - b*dC[:-1] - c*dC[1:])/C
            r.countrate_twoomit = a
            
            # best-fit chi squared
            r.chisq_twoomit = A + a**2*C + b**2*Cinv_diag[:-1] + c**2*Cinv_diag[1:]
            r.chisq_twoomit -= 2*a*B + 2*b*dB[:-1] + 2*c*dB[1:]
            r.chisq_twoomit += 2*a*b*dC[:-1] + 2*a*c*dC[1:] + 2*b*c*Cinv_offdiag
            r.chisq_twoomit /= scale

            # uncertainty on the slope from inverting the (a, b, c)
            # covariance matrix
            fac = Cinv_diag[1:]*Cinv_diag[:-1] - Cinv_offdiag**2
            term2 = dC[:-1]*(dC[:-1]*Cinv_diag[1:] - Cinv_offdiag*dC[1:])
            term3 = dC[1:]*(dC[:-1]*Cinv_offdiag - Cinv_diag[:-1]*dC[1:])
            r.uncert_twoomit = np.sqrt(fac/(C*fac - term2 + term3))
            r.uncert_twoomit *= np.sqrt(scale)
        
        r.fill_masked_reads(diffs2use)            
            
    return r




def mask_jumps(diffs, Cov, sig, threshold_oneomit=20.25,
               threshold_twoomit=23.8, diffs2use=None):

    """

    Function mask_jumps implements a likelihood-based, iterative jump
    detection algorithm.

    Parameters
    ----------
    diffs : array_like
        Resultant differences.
    Cov : Covar
        Class holding the covariance matrix information. Must be based on differences alone (without the pedestal).
    sig : array_like, shape (npix)
        Read noise.
    threshold_oneomit : float, optional
        Minimum chi-squared improvement to exclude a single resultant difference. Default is 20.25.
    threshold_twoomit : float, optional
        Minimum chi-squared improvement to exclude two sequential resultant differences. Default is 23.8.
    diffs2use : array_like, shape same as diffs, optional
        Mask array indicating which resultant differences are okay (1) or contaminated (0). Default is None.

    Returns
    -------
    diffs2use : array_like, shape same as diffs
        Mask array of resultant differences after jump detection.
    countrates : array_like
        Count rates after masking pixels and resultants in diffs2use.


    """

    if Cov.pedestal:
        raise ValueError("Cannot mask jumps with a Covar class that includes a pedestal fit.")
    
    # Force a copy of the input array for more efficient memory access.
    
    d = diffs*1
    
    # We can use one-omit searches only where the reads immediately
    # preceding and following have just one read.  If a readout
    # pattern has more than one read per resultant but significant
    # gaps between resultants then a one-omit search might still be a
    # good idea even with multiple-read resultants.

    oneomit_ok = Cov.Nreads[1:]*Cov.Nreads[:-1] >= 1
    oneomit_ok[0] = oneomit_ok[-1] = True

    # Other than that, we need to omit two.  If a resultant has more
    # than two reads, we need to omit both differences containing it
    # (one pair of omissions in the differences).

    twoomit_ok = Cov.Nreads[1:-1] > 1
    
    # This is the array to return: one for resultant differences to
    # use, zero for resultant differences to ignore.

    if diffs2use is None:
        diffs2use = np.ones(d.shape, np.uint8)

    # We need to estimate the covariance matrix.  I'll use the median
    # here for now to limit problems with the count rate in reads with
    # jumps (which is what we are looking for) since we'll be using
    # likelihoods and chi squared; getting the covariance matrix
    # reasonably close to correct is important.
    
    countrateguess = np.median(d, axis=0)[np.newaxis, :]
    countrateguess *= countrateguess > 0

    # boolean arrays to be used later
    recheck = np.ones(d.shape[1]) == 1
    dropped = np.ones(d.shape[1]) == 0
    
    for j in range(d.shape[0]):

        # No need for indexing on the first pass.
        if j == 0:
            result = fit_ramps(d, Cov, sig, countrateguess=countrateguess, 
                               diffs2use=diffs2use, detect_jumps=True)
            # Also save the count rates so that we can use them later
            # for debiasing.
            countrate = result.countrate*1.
        else:
            result = fit_ramps(d[:, recheck], Cov, sig[recheck],
                               countrateguess=countrateguess[:, recheck], 
                               diffs2use=diffs2use[:, recheck],
                               detect_jumps=True)

        # Chi squared improvements
        
        dchisq_two = result.chisq - result.chisq_twoomit
        dchisq_one = result.chisq - result.chisq_oneomit

        # We want the largest chi squared difference

        best_dchisq_one = np.amax(dchisq_one*oneomit_ok[:, np.newaxis], axis=0)
        best_dchisq_two = np.amax(dchisq_two*twoomit_ok[:, np.newaxis], axis=0)
        
        # Is the best improvement from dropping one resultant
        # difference or two?  Two drops will always offer more
        # improvement than one so penalize them by the respective
        # thresholds.  Then find the chi squared improvement
        # corresponding to dropping either one or two reads, whichever
        # is better, if either exceeded the threshold.

        onedropbetter = (best_dchisq_one - threshold_oneomit > best_dchisq_two - threshold_twoomit)
        
        best_dchisq = best_dchisq_one*(best_dchisq_one > threshold_oneomit)*onedropbetter
        best_dchisq += best_dchisq_two*(best_dchisq_two > threshold_twoomit)*(~onedropbetter)

        # If nothing exceeded the threshold set the improvement to
        # NaN so that dchisq==best_dchisq is guaranteed to be False.
        
        best_dchisq[best_dchisq == 0] = np.nan

        # Now make the masks for which resultant difference(s) to
        # drop, count the number of ramps affected, and drop them.
        # If no ramps were affected break the loop.

        dropone = dchisq_one == best_dchisq
        droptwo = dchisq_two == best_dchisq

        drop = np.any([np.sum(dropone, axis=0),
                       np.sum(droptwo, axis=0)], axis=0)
        
        if np.sum(drop) == 0:
            break

        # Store the updated counts with omitted reads
        
        new_cts = np.zeros(np.sum(recheck))
        i_d1 = np.sum(dropone, axis=0) > 0
        new_cts[i_d1] = np.sum(result.countrate_oneomit*dropone, axis=0)[i_d1]
        i_d2 = np.sum(droptwo, axis=0) > 0
        new_cts[i_d2] = np.sum(result.countrate_twoomit*droptwo, axis=0)[i_d2]

        # zero out count rates with drops and add their new values back in
        
        countrate[recheck] *= drop == 0
        countrate[recheck] += new_cts
        
        # Drop the read (set diffs2use=0) if the boolean array is True.
        
        diffs2use[:, recheck] *= ~dropone
        diffs2use[:-1, recheck] *= ~droptwo
        diffs2use[1:, recheck] *= ~droptwo

        # No need to repeat this on the entire ramp, only re-search
        # ramps that had a resultant difference dropped this time.

        dropped[:] = False
        dropped[recheck] = drop
        recheck[:] = dropped

        # Do not try to search for bad resultants if we have already
        # given up on all but one, two, or three resultant differences
        # in the ramp.  If there are only two left we have no way of
        # choosing which one is "good".  If there are three left we
        # run into trouble in case we need to discard two.

        recheck[np.sum(diffs2use, axis=0) <= 3] = False

    return diffs2use, countrate



def getramps(countrate, sig, readtimes, nramps=10):

    """
    Function getramps: make some synthetic ramps
    
    Parameters
    ----------
    countrate : float or array_like
        Electrons per unit time.
    sig : float
        Single-read read noise in electrons.
    readtimes : list or list of lists
        Times of reads. If a list of lists, times are averaged together to produce a resultant.
    nramps : int, optional
        Number of ramps desired. Default is 10.

    Returns
    -------
    counts : ndarray, shape (nreads, nramps)
        Electrons in each read.

    """

    t_last = 0
    counts = np.zeros((len(readtimes), nramps))  # resultant values to return
    counts_total = np.zeros(nramps)  # Running total of electrons

    for k in range(len(readtimes)):
        t = readtimes[k]
        counts_last = counts_total*1.
        counts_resultant = counts_last*0
        
        if hasattr(t, "__len__"):
            for i in range(len(t)):
                lam = countrate*(t[i] - t_last) # expected number of electrons
                counts_total += np.random.poisson(lam, nramps)
                counts[k] += counts_total/len(t)
                t_last = t[i]
                
            # add read noise
            counts[k] += np.random.randn(nramps)*sig/np.sqrt(len(t))
            
        else:
            if t_last is None:
                t_last = t
            lam = countrate*(t - t_last) # expected number of electrons
            counts_total += np.random.poisson(lam, nramps)
            counts[k] = counts_total
            t_last = t
            
            # add read noise
            counts[k] += np.random.randn(nramps)*sig
        
    return counts