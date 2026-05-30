# Author: Tim Brandt
# Shared with HISPEC team in Aug 2025
#
# Reference:
# Brandt, T. D., "Likelihood-based Jump Detection and Cosmic Ray Rejection for Detectors Read Out Up-the-ramp", PASP, 136, 045005 (2024)
# https://ui.adsabs.harvard.edu/abs/2024PASP..136d5005B/abstract

import cython
import numpy as np
from cpython.mem cimport PyMem_Malloc, PyMem_Free


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)

def fit_ramps(double [:, :] diffs,
              char [:, :] diffs2use,
              double [:] alpha_phnoise,
              double [:] beta_phnoise,
              double [:] alpha_readnoise,
              double [:] beta_readnoise,
              double sig,
              double [:] countrateguess,
              int nramps,
              int ndiffs):

    cdef extern from "math.h":
        double log(double x) nogil
        double sqrt(double x) nogil
        
    cdef int i, j
    
    cdef double *alpha = <double *> PyMem_Malloc(ndiffs * sizeof(double))
    cdef double *beta = <double *> PyMem_Malloc(ndiffs * sizeof(double))

    cdef double *d = <double *> PyMem_Malloc(ndiffs * sizeof(double))
    
    cdef double *phi = <double *> PyMem_Malloc((ndiffs + 1) * sizeof(double))
    cdef double *Phi = <double *> PyMem_Malloc(ndiffs * sizeof(double))
    cdef char *d2u = <char *> PyMem_Malloc(ndiffs * sizeof(char))

    A_np = np.empty(nramps)
    cdef double [:] A = A_np
    B_np = np.empty(nramps)
    cdef double [:] B = B_np
    C_np = np.empty(nramps)
    cdef double [:] C = C_np
    countrate_np = np.empty(nramps)
    cdef double [:] countrate = countrate_np
    chisq_np = np.empty(nramps)
    cdef double [:] chisq = chisq_np
    uncert_np = np.empty(nramps)
    cdef double [:] uncert = uncert_np
    logdetC_np = np.empty(nramps)
    cdef double [:] logdetC = logdetC_np
    
    phi[ndiffs] = 1
    Phi[ndiffs - 1] = 0
    
    cdef double scale, iscale, logscale #= log(scale)

    cdef double Theta_im1, theta_im1, theta_im2, theta_i, Theta_i, ThetaD_i
    cdef double Phi_ip1, phi_ip1, phi_ip2, phi_i, Phi_i
    cdef double theta_0, theta_1, Theta_0, Theta_1, ThetaD_0, ThetaD_1, theta_n
    cdef double _A, _B, _C
    cdef double iT, dC, iC, ctrtguess, rnvar, sgn
    cdef char d2u_i, d2u_ip1
    
    theta_0 = 1
    Theta_0 = -1
    ThetaD_0 = 0
        
    for j in range(nramps):

        scale = countrateguess[j]*alpha_phnoise[0] + sig**2*alpha_readnoise[0]
        logscale = log(scale)
        iscale = 1./scale
        
        ctrtguess = iscale*countrateguess[j]
        rnvar = iscale*sig**2

        d2u_ip1 = diffs2use[0, j]
        
        for i in range(ndiffs):
            d2u_i = d2u_ip1
            d2u[i] = d2u_i
            alpha[i] = ctrtguess*alpha_phnoise[i] + rnvar*alpha_readnoise[i]
            d[i] = diffs[i, j]*d2u_i
            
            if i < ndiffs - 1:
                d2u_ip1 = diffs2use[i + 1, j]
                beta[i] = d2u_i*d2u_ip1*(ctrtguess*beta_phnoise[i] +
                                         rnvar*beta_readnoise[i])
                
        phi[ndiffs - 1] = alpha[ndiffs - 1]
        phi_ip2 = phi[ndiffs]
        phi_ip1 = phi[ndiffs - 1]
        Phi_ip1 = Phi[ndiffs - 1]

        # sgn is negative for even indices
        sgn = 2*((ndiffs - 1)%2) - 1
        
        for i in range(ndiffs - 2, -1, -1):
            phi_i = alpha[i]*phi_ip1 - beta[i]**2*phi_ip2
            Phi_i = beta[i]*(Phi_ip1 + sgn*phi_ip2)
            Phi[i] = Phi_i
            phi[i] = phi_i
            phi_ip2 = phi_ip1
            phi_ip1 = phi_i
            Phi_ip1 = Phi_i
            sgn *= -1

        theta_1 = alpha[0]
        Theta_1 = -beta[0] + theta_1
        ThetaD_1 = -d[0]
        
        theta_im2 = theta_0
        theta_im1 = theta_1
        Theta_im1 = Theta_1

        ThetaD_i = ThetaD_1
        ThetaD_i = beta[0]*ThetaD_i + d[1]*theta_1

        _A = d[0]*phi[1]*(-2*ThetaD_0 + d[0]*theta_0)
        dC = -(phi[1]*Theta_0 + theta_0*Phi[0])*d2u[0]
        
        _B = d[0]*dC
        _C = dC

        _A = _A + d[1]*phi[2]*(2*beta[0]*ThetaD_1 + d[1]*theta_1)
        dC = (phi[2]*Theta_1 + theta_1*Phi[1])*d2u[1]
        
        _B = _B + d[1]*dC
        _C = _C + dC

        sgn = -1  # -1 for index 0, 1 for index 1, -1 for index 2
        for i in range(2, ndiffs):
            
            theta_i = alpha[i - 1]*theta_im1 - beta[i - 2]**2*theta_im2
            theta_im2 = theta_im1
            theta_im1 = theta_i
            
            Theta_i = Theta_im1*beta[i - 1] + sgn*theta_i
            Theta_im1 = Theta_i
            
            _A = _A + d[i]*phi[i + 1]*(2*sgn*beta[i - 1]*ThetaD_i + d[i]*theta_i)
            dC = sgn*(phi[i + 1]*Theta_i + theta_i*Phi[i])*d2u[i]
            _B = _B + d[i]*dC
            _C = _C + dC
            
            ThetaD_i = beta[i - 1]*ThetaD_i + sgn*d[i]*theta_i
            sgn = -1*sgn
            
        theta_n = alpha[ndiffs - 1]*theta_im1 - beta[ndiffs - 2]**2*theta_im2
            
        iT = 1./theta_n
        
        A[j] = _A*iT*iscale
        B[j] = _B*iT*iscale
        C[j] = _C*iT*iscale

        iC = 1/C[j]
        
        countrate[j] = B[j]*iC
        chisq[j] = A[j] - B[j]**2*iC
        uncert[j] = sqrt(iC)

        logdetC[j] = -log(iT) + ndiffs*logscale
        
    PyMem_Free(alpha)
    PyMem_Free(beta)
    PyMem_Free(d)
    PyMem_Free(phi)
    PyMem_Free(Phi)
    PyMem_Free(d2u)
    
    return logdetC_np, A_np, B_np, C_np, countrate_np, chisq_np, uncert_np




@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)

def logsum(double [:] x, int n):

    cdef extern from "math.h":
        double log(double x)

    cdef double x1, x2
    cdef int i, j, i0, niter
    cdef dn = 20
    
    niter = int(n/dn)

    x2 = 0
    for i in range(niter):
        i0 = i*dn
        x1 = 1

        for j in range(dn):
            x1 *= x[i0 + j]

        x2 += log(x1)
        
    x1 = 1       
    for j in range(dn*niter, n):
        x1 *= x[j]

    x2 += log(x1)

    return x2

# minor update to the function by JB Ruffio from the original by Tim Brandt to have the read noise (sig) and the gain being an array instead of a scalar.
# alpha_phnoise and beta_phnoise are now normalized by the gain inside this function instead of outside.
# this is to be enable the ramp fitting for rows of a 2D detector image where each pixel can have its own read noise
def fit_ramps_row(double [:, :] diffs,
              char [:, :] diffs2use,
              double [:] alpha_phnoise,
              double [:] beta_phnoise,
              double [:] alpha_readnoise,
              double [:] beta_readnoise,
              double [:] sigs,
              double [:] gains,
              double [:] countrateguess,
              int nramps,
              int ndiffs):
    cdef extern from "math.h":
        double log(double x) nogil
        double sqrt(double x) nogil

    cdef int i, j

    cdef double *alpha = <double *> PyMem_Malloc(ndiffs * sizeof(double))
    cdef double *beta = <double *> PyMem_Malloc(ndiffs * sizeof(double))

    cdef double *d = <double *> PyMem_Malloc(ndiffs * sizeof(double))

    cdef double *phi = <double *> PyMem_Malloc((ndiffs + 1) * sizeof(double))
    cdef double *Phi = <double *> PyMem_Malloc(ndiffs * sizeof(double))
    cdef char *d2u = <char *> PyMem_Malloc(ndiffs * sizeof(char))

    A_np = np.empty(nramps)
    cdef double [:] A = A_np
    B_np = np.empty(nramps)
    cdef double [:] B = B_np
    C_np = np.empty(nramps)
    cdef double [:] C = C_np
    countrate_np = np.empty(nramps)
    cdef double [:] countrate = countrate_np
    chisq_np = np.empty(nramps)
    cdef double [:] chisq = chisq_np
    uncert_np = np.empty(nramps)
    cdef double [:] uncert = uncert_np
    logdetC_np = np.empty(nramps)
    cdef double [:] logdetC = logdetC_np

    phi[ndiffs] = 1
    Phi[ndiffs - 1] = 0

    cdef double scale, iscale, logscale  #= log(scale)

    cdef double Theta_im1, theta_im1, theta_im2, theta_i, Theta_i, ThetaD_i
    cdef double Phi_ip1, phi_ip1, phi_ip2, phi_i, Phi_i
    cdef double theta_0, theta_1, Theta_0, Theta_1, ThetaD_0, ThetaD_1, theta_n
    cdef double _A, _B, _C
    cdef double iT, dC, iC, ctrtguess, rnvar, sgn
    cdef char d2u_i, d2u_ip1

    theta_0 = 1
    Theta_0 = -1
    ThetaD_0 = 0

    for j in range(nramps):

        scale = countrateguess[j] * alpha_phnoise[0]/gains[j] + sigs[j] ** 2 * alpha_readnoise[0]
        logscale = log(scale)
        iscale = 1. / scale

        ctrtguess = iscale * countrateguess[j]
        rnvar = iscale * sigs[j] ** 2

        d2u_ip1 = diffs2use[0, j]

        for i in range(ndiffs):
            d2u_i = d2u_ip1
            d2u[i] = d2u_i
            alpha[i] = ctrtguess * alpha_phnoise[i]/gains[j] + rnvar * alpha_readnoise[i]
            d[i] = diffs[i, j] * d2u_i

            if i < ndiffs - 1:
                d2u_ip1 = diffs2use[i + 1, j]
                beta[i] = d2u_i * d2u_ip1 * (ctrtguess * beta_phnoise[i]/gains[j] +
                                             rnvar * beta_readnoise[i])

        phi[ndiffs - 1] = alpha[ndiffs - 1]
        phi_ip2 = phi[ndiffs]
        phi_ip1 = phi[ndiffs - 1]
        Phi_ip1 = Phi[ndiffs - 1]

        # sgn is negative for even indices
        sgn = 2 * ((ndiffs - 1) % 2) - 1

        for i in range(ndiffs - 2, -1, -1):
            phi_i = alpha[i] * phi_ip1 - beta[i] ** 2 * phi_ip2
            Phi_i = beta[i] * (Phi_ip1 + sgn * phi_ip2)
            Phi[i] = Phi_i
            phi[i] = phi_i
            phi_ip2 = phi_ip1
            phi_ip1 = phi_i
            Phi_ip1 = Phi_i
            sgn *= -1

        theta_1 = alpha[0]
        Theta_1 = -beta[0] + theta_1
        ThetaD_1 = -d[0]

        theta_im2 = theta_0
        theta_im1 = theta_1
        Theta_im1 = Theta_1

        ThetaD_i = ThetaD_1
        ThetaD_i = beta[0] * ThetaD_i + d[1] * theta_1

        _A = d[0] * phi[1] * (-2 * ThetaD_0 + d[0] * theta_0)
        dC = -(phi[1] * Theta_0 + theta_0 * Phi[0]) * d2u[0]

        _B = d[0] * dC
        _C = dC

        _A = _A + d[1] * phi[2] * (2 * beta[0] * ThetaD_1 + d[1] * theta_1)
        dC = (phi[2] * Theta_1 + theta_1 * Phi[1]) * d2u[1]

        _B = _B + d[1] * dC
        _C = _C + dC

        sgn = -1  # -1 for index 0, 1 for index 1, -1 for index 2
        for i in range(2, ndiffs):
            theta_i = alpha[i - 1] * theta_im1 - beta[i - 2] ** 2 * theta_im2
            theta_im2 = theta_im1
            theta_im1 = theta_i

            Theta_i = Theta_im1 * beta[i - 1] + sgn * theta_i
            Theta_im1 = Theta_i

            _A = _A + d[i] * phi[i + 1] * (2 * sgn * beta[i - 1] * ThetaD_i + d[i] * theta_i)
            dC = sgn * (phi[i + 1] * Theta_i + theta_i * Phi[i]) * d2u[i]
            _B = _B + d[i] * dC
            _C = _C + dC

            ThetaD_i = beta[i - 1] * ThetaD_i + sgn * d[i] * theta_i
            sgn = -1 * sgn

        theta_n = alpha[ndiffs - 1] * theta_im1 - beta[ndiffs - 2] ** 2 * theta_im2

        iT = 1. / theta_n

        A[j] = _A * iT * iscale
        B[j] = _B * iT * iscale
        C[j] = _C * iT * iscale

        iC = 1 / C[j]

        countrate[j] = B[j] * iC
        chisq[j] = A[j] - B[j] ** 2 * iC
        uncert[j] = sqrt(iC)

        logdetC[j] = -log(iT) + ndiffs * logscale

    PyMem_Free(alpha)
    PyMem_Free(beta)
    PyMem_Free(d)
    PyMem_Free(phi)
    PyMem_Free(Phi)
    PyMem_Free(d2u)

    return logdetC_np, A_np, B_np, C_np, countrate_np, chisq_np, uncert_np