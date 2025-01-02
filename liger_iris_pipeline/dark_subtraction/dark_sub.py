#
#  Module for dark subtracting science data sets
#

import numpy as np
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def do_correction(input_model, dark_model, dark_output=None):
    """
    Short Summary
    -------------
    Execute all tasks for Dark Current Subtraction

    Parameters
    ----------
    input_model: data model object
        science data to be corrected

    dark_model: dark model object
        dark data

    dark_output: string
        file name in which to optionally save averaged dark data

    Returns
    -------
    output_model: data model object
        dark-subtracted science data

    """

    # Save some data params for easy use later
    instrument = input_model.meta.instrument.name

    # Replace NaN's in the dark with zeros
    dark_model.data[np.isnan(dark_model.data)] = 0.0

    output_model = subtract_dark(input_model, dark_model)

    # If the user requested to have the dark file saved,
    # save the reference model as this file. This will
    # ensure consistency from the user's standpoint
    if dark_output is not None:
        log.info("Writing dark current data to %s", dark_output)
        dark_model.save(dark_output)

    output_model.meta.cal_step.dark_sub = "COMPLETE"

    return output_model


def subtract_dark(input, dark):
    """
    Subtracts dark current data from science arrays, combines
    error arrays in quadrature, and updates data quality array based on
    DQ flags in the dark arrays.

    Parameters
    ----------
    input: data model object
        the input science data

    dark: dark model object
        the dark current data

    Returns
    -------
    output: data model object
        dark-subtracted science data

    """

    log.debug("subtract_dark: size=%d,%d", input.data.shape[0], input.data.shape[1])

    # Create output as a copy of the input science data model
    output = input.copy()

    # All other instruments have a single 2D dark DQ array
    darkdq = dark.dq

    # Combine the dark and science DQ data
    output.dq = np.bitwise_or(input.dq, darkdq)

    output.data -= dark.data

    # combine the ERR arrays in quadrature
    # NOTE: currently stubbed out until ERR handling is decided
    # output.err[i,j] = np.sqrt(
    #           output.err[i,j]**2 + dark.err[j]**2)

    return output
