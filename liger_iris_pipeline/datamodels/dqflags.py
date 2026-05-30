import numpy as np

__all__ = ['DQ_FLAGS']

# Detector pixel quality flags
DQ_FLAGS = {
    'GOOD':             np.uint32(0),      # No bits set, all is good
    'DO_NOT_USE':       np.uint32(2**0),   # Bad pixel. Do not use.
    'SATURATED':        np.uint32(2**1),   # Pixel saturated during exposure
    'JUMP_DET':         np.uint32(2**2),   # Jump detected during exposure
    'DROPOUT':          np.uint32(2**3),   # Data lost in transmission
    'OUTLIER':          np.uint32(2**4),   # Flagged by outlier detection
    'PERSISTENCE':      np.uint32(2**5),   # High persistence
    'AD_FLOOR':         np.uint32(2**6),   # Below A/D floor (0 DN)
    'CHARGELOSS':       np.uint32(2**7),   # Charge migration
    'SUBARRAY':         np.uint32(2**8),   # Is subarray
    'NON_SCIENCE':      np.uint32(2**9),   # Pixel not on science portion of detector
    'DEAD':             np.uint32(2**10),  # Dead pixel
    'HOT':              np.uint32(2**11),  # Hot pixel
    'WARM':             np.uint32(2**12),  # Warm pixel
    'LOW_QE':           np.uint32(2**13),  # Low quantum efficiency
    'COLD':             np.uint32(2**14),  # Cold pixel
    'TELEGRAPH':        np.uint32(2**15),  # Telegraph pixel
    'NONLINEAR':        np.uint32(2**16),  # Pixel highly nonlinear
    'BAD_REF_PIXEL':    np.uint32(2**17),  # Reference pixel cannot be used
    'NO_FLAT_FIELD':    np.uint32(2**18),  # Flat field cannot be measured
    'NO_GAIN_VALUE':    np.uint32(2**19),  # Gain cannot be measured
    'NO_LIN_CORR':      np.uint32(2**20),  # Linearity correction not available
    'NO_SAT_CHECK':     np.uint32(2**21),  # Saturation check not available
    'UNRELIABLE_BIAS':  np.uint32(2**22),  # Bias variance large
    'UNRELIABLE_DARK':  np.uint32(2**23),  # Dark variance large
    'UNRELIABLE_SLOPE': np.uint32(2**24),  # Slope variance large (i.e., noisy pixel)
    'UNRELIABLE_FLAT':  np.uint32(2**25),  # Flat variance large
    'UNRELIABLE_WS':    np.uint32(2**26),  # Unreliable wavelength solution
    'FLUX_ESTIMATED':   np.uint32(2**27),  # Pixel flux estimated due to missing/bad data
    'TELLURIC':         np.uint32(2**28),  # Telluric absorption line
    'OH_LINE':          np.uint32(2**29),  # OH emission line
    'CROSS_BAD':        np.uint32(2**30),  # Cross-shaped bad pixel
    'REFERENCE_PIXEL':  np.uint32(2**31),  # Pixel is a reference pixel
}