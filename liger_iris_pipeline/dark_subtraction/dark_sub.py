#
#  Module for dark subtracting science data sets
#

import numpy as np
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def subtract_dark(input_model, dark_model):
    """
    Subtract dark current data from the input science data model.

    Args:

    """
    output_model = input_model.copy()

    # Combine the dark and science DQ data
    output_model.dq = np.bitwise_or(input_model.dq, dark_model.dq)

    # Subtract (e-)
    output_model.data -= dark_model.data

    # Error
    if input_model.err is not None and dark_model.err is not None:
        output_model.err = np.sqrt(input_model.err**2 + dark_model.err**2)

    # Data quality
    if input_model.dq is not None and dark_model.dq is not None:
        output_model.dq = np.bitwise_or(input_model.dq, dark_model.dq)

    # Return
    return output_model