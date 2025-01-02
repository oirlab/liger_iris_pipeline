import numpy as np
import logging
import scipy.stats

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def do_correction(input_model, method="median"):
    """
    Short Summary
    -------------
    Normalize a frame by dividing by its own mean or median

    Parameters
    ----------

    input_model: data model object
        the input science data

    method: string
        name of numpy method to use for normalization, e.g.
        median (default) or mean

    Returns
    -------
    output_model: data model object
        normalized frame

    """

    output_model = apply_norm(input_model, method)

    output_model.meta.cal_step.normalize = "COMPLETE"

    return output_model


def apply_norm(input, method):
    """
    Divides the input frame by its own median, mean, or mode
    based on the method string.

    Parameters
    ----------
    input: data model object
        the input science data

    method: string
        name of numpy method to use for normalization, e.g.
        median (default) or mean
        mode uses `scipy.stats.mode`

    Returns
    -------
    output: data model object
        normalized frame

    """

    log.debug("normalize: size=%d,%d", input.data.shape[0], input.data.shape[1])

    # Create output as a copy of the input science data model
    output = input.copy()

    if method is None:
        norm_factor = 1
    elif method == "mean":
        norm_factor = np.mean(input.data)
    elif method == "median":
        norm_factor = np.median(input.data)
    elif method == "mode":
        norm_factor = scipy.stats.mode(input.data, axis=None).mode

    log.info("running normalize with method %s", method)
    output.data /= norm_factor
    output.err /= norm_factor

    return output
