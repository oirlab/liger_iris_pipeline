

import numpy as np
from numba import njit

@njit
def nanmad(x):
    return np.nanmedian(np.abs(x - np.nanmedian(x)))

def weighted_stddev(x, w):
    bias_estimator = np.nansum(w) / (np.nansum(w)**2 - np.nansum(w**2))
    return np.sqrt(np.nansum(w * (x - np.nanmean(x))**2) * bias_estimator)



def estimate_uniform_sky_background_imager(
        image : np.ndarray, err : np.ndarray,
        background_percentile : float = 0.1,
        n_sigma : float = 3.0
    ) -> tuple[np.ndarray, np.ndarray]:
    """
    """

    # Get the sky value
    sky = np.nanquantile(image, background_percentile)
    mask = np.where(np.isfinite(image))

    # Iteratively compute
    for i in range(100):
        if len(mask[0]) <= 1 / background_percentile: # Fix this line
            break
        resn = (image[mask] - sky[mask]) / err[mask]
        sigma = nanmad(resn) * 1.4826
        mask = np.abs(resn) < sigma * n_sigma
        n_pix = np.sum(mask)
        sky = np.median(image[mask])
        res = (image[mask] - sky) / err[mask]
        sky_err = np.sum(res**2) / np.sqrt(n_pix)

    return sky, sky_err, mask