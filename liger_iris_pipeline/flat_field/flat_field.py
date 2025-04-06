#
#  Module for applying flat fielding
#

import logging

import numpy as np

from ..utils.subarray import get_subarray_model
from .. import datamodels
from ..datamodels import dqflags

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def apply_flatfield(input_model, flat_model):

    # Find pixels in the flat that have a value of NaN and set
    # their DQ to NO_FLAT_FIELD
    flat_data = flat_model.data.copy()
    flat_dq = flat_model.dq.copy()
    flat_nan = np.isnan(flat_data)
    flat_dq[flat_nan] = np.bitwise_or(flat_model.dq[flat_nan], dqflags.pixel["NO_FLAT_FIELD"])

    # Find pixels in the flat have have a value of zero, and set
    # their DQ to NO_FLAT_FIELD
    flat_zero = np.where(flat_data == 0.0)
    flat_dq[flat_zero] = np.bitwise_or(flat_dq[flat_zero], dqflags.pixel["NO_FLAT_FIELD"])

    # Find all pixels in the flat that have a DQ value of NO_FLAT_FIELD
    flat_bad = np.bitwise_and(flat_dq, dqflags.pixel["NO_FLAT_FIELD"])

    # Reset the flat value of all bad pixels to 1.0, so that no
    # correction is made
    flat_data[np.where(flat_bad)] = 1.0

    # Error propagation
    if hasattr(input_model, 'err'):
        input_model.err = np.sqrt(input_model.err**2 + (input_model.data * flat_model.err / flat_model.data)**2) / flat_data

    # Data quality
    if hasattr(input_model, 'dq'):
        input_model.dq |= flat_model.dq

    # Apply the flat field correction
    input_model.data = input_model.data / flat_data
    
    return input_model