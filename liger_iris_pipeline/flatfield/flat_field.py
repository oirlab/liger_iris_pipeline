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

def do_correction(
    input_model, flat_model
):
    """Flat-field a JWST data model using a flat-field model

    Parameters
    ----------
    input_model : JWST data model
        Input science data model to be flat-fielded.

    flat_model : JWST data model, or None
        Data model containing flat-field for all instruments other than
        NIRSpec spectrographic data.

    Returns
    -------
    output_model : data model
        The data model for the flat-fielded science data.

    interpolated_flats : data model or None
        If not None, this will be a MultiSlitModel containing the
        interpolated flat fields (NIRSpec data only).
    """

    # Initialize the output model as a copy of the input
    output_model = input_model.copy()

    do_flat_field(output_model, flat_model)

    return output_model


#
# These functions are for non-NIRSpec flat fielding, or for NIRSpec imaging.
#


def do_flat_field(output_model, flat_model):
    """Apply flat-fielding for non-NIRSpec modes, updating the output model.

    Parameters
    ----------
    output_model : JWST data model
        flat-fielded input science data model, modified in-place

    flat_model : JWST data model
        data model containing flat-field
    """
    log.debug("Flat field correction ")
    apply_flat_field(output_model, flat_model)
    
def apply_flat_field(science, flat):
    """Flat field the data and error arrays.

    Extended summary
    ----------------
    The science data and error arrays will be divided by the flat field.
    The data quality array will be updated based on bad pixels in flat
    field arrays. Applies portion of flat field corresponding to science
    image subarray.

    Parameters
    ----------
    science : JWST data model
        input science data model

    flat : JWST data model
        flat field data model
    """

    # Extract subarray from reference data, if necessary
    #if reffile_utils.ref_matches_sci(science, flat):
    if science.meta.subarray.name == flat.meta.subarray.name:
        flat_data = flat.data
        flat_dq = flat.dq
    else:
        log.info("Extracting matching subarray from flat")
        sub_flat = get_subarray_model(science, flat)
        flat_data = sub_flat.data.copy()
        flat_dq = sub_flat.dq.copy()
        sub_flat.close()

    # Find pixels in the flat that have a value of NaN and set
    # their DQ to NO_FLAT_FIELD
    flat_nan = np.isnan(flat_data)
    flat_dq[flat_nan] = np.bitwise_or(flat_dq[flat_nan], dqflags.pixel["NO_FLAT_FIELD"])

    # Find pixels in the flat have have a value of zero, and set
    # their DQ to NO_FLAT_FIELD
    flat_zero = np.where(flat_data == 0.0)
    flat_dq[flat_zero] = np.bitwise_or(
        flat_dq[flat_zero], dqflags.pixel["NO_FLAT_FIELD"]
    )

    # Find all pixels in the flat that have a DQ value of NO_FLAT_FIELD
    flat_bad = np.bitwise_and(flat_dq, dqflags.pixel["NO_FLAT_FIELD"])

    # Reset the flat value of all bad pixels to 1.0, so that no
    # correction is made
    flat_data[np.where(flat_bad)] = 1.0
    science.data /= flat_data
    science.err /= flat_data

    # Combine the science and flat DQ arrays
    science.dq = np.bitwise_or(science.dq, flat_dq)
