import math
import numpy as np

from jwst import datamodels
import liger_iris_pipeline
from . import subtract_images
from jwst.assign_wcs.util import create_grism_bbox
from astropy.stats import sigma_clip

from ..utils.subarray import get_subarray_model

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def background_sub(input_model, bkg_list, sigma, maxiters):

    """
    Short Summary
    -------------
    Subtract the background signal from an exposure by subtracting
    the average of one or more background exposures from it.

    Parameters
    ----------
    input_model: data model
        input target exposure data model

    bkg_list: filename list
        list of background exposure file names

    Returns
    -------
    result: data model
        background-subtracted target data model

    """

    # Compute the average of the background images associated with
    # the target exposure
    bkg_model = average_background(bkg_list, sigma, maxiters)

    bkg_model = get_subarray_model(input_model, bkg_model)

    # Subtract the average background from the member
    log.debug(" subtracting avg bkg from {}".format(input_model.meta.filename))
    result = subtract_images.subtract(input_model, bkg_model)

    # Close the average background image and update the step status
    bkg_model.close()

    # We're done. Return the result.
    return result


def average_background(bkg_list, sigma, maxiters):

    """
    Average multiple background exposures into a combined data model

    Parameters:
    -----------

    bkg_list: filename list
        List of background exposure file names

    Returns:
    --------

    avg_bkg: data model
        The averaged background exposure

    """

    num_bkg = len(bkg_list)
    avg_bkg = None
    cdata = None

    # Loop over the images to be used as background
    for i, bkg_file in enumerate(bkg_list):
        log.debug(" Accumulate bkg from {}".format(bkg_file))
        bkg_model = liger_iris_pipeline.ImagerModel(bkg_file)

        # Initialize the avg_bkg model, if necessary
        if avg_bkg is None:
            avg_bkg = liger_iris_pipeline.ImagerModel(bkg_model.shape)

        if cdata is None:
            cdata = np.zeros(((num_bkg,) + bkg_model.shape))
            cerr = cdata.copy()

        # Accumulate the data from this background image
        cdata[i] = bkg_model.data
        cerr[i] = bkg_model.err * bkg_model.err
        avg_bkg.dq = np.bitwise_or(avg_bkg.dq, bkg_model.dq)

        bkg_model.close()

    # Clip the background data
    log.debug(" clip with sigma={} maxiters={}".format(sigma, maxiters))
    mdata = sigma_clip(cdata, sigma=sigma, maxiters=maxiters, axis=0)

    # Compute the mean of the non-clipped values
    avg_bkg.data = mdata.mean(axis=0).data

    # Mask the ERR values using the data mask
    merr = np.ma.masked_array(cerr, mask=mdata.mask)

    # Compute the combined ERR as the uncertainty in the mean
    avg_bkg.err = np.sqrt(merr.sum(axis=0)) / (num_bkg - merr.mask.sum(axis=0))

    return avg_bkg
