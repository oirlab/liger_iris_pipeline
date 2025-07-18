from pathlib import Path
import sys
import os
import warnings

import numpy as np
from astropy.io import fits

import asdf
from stdatamodels import filetype
from stdatamodels.model_base import _FileReference

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

def open(init=None, memmap : bool = False, copy : bool = False, **kwargs):
    """
    Creates a DataModel from a number of different types.

    Args:
        init (None | tuple | str | file object | astropy.io.fits.HDUList | numpy.ndarray | dict):
            The input used to initialize the model:
            
            - **None**: A default data model with no shape.
            - **tuple**: A shape tuple to initialize empty data.
            - **str**: A file path to load data from (FITS, JSON, or ASDF).
            - **file object**: A readable file object.
            - **astropy.io.fits.HDUList**: Initialize from an `~astropy.io.fits.HDUList`.
            - **numpy.ndarray**: A NumPy array to initialize the data.
            - **dict**: An object model tree for the data model.

        memmap: (bool) (Turn memmap of file on or off.  (default: False).
        
        kwargs (dict): Additional arguments used to initialize the model.
            - **validate_arrays** (bool): If `True`, arrays will be validated against ndim, max_ndim, and datatype validators in the schemas.
    
    Returns:
        LigerIRISDataModel : The specific LigerIRISDataModel instance.
    """

    from .model_base import LigerIRISDataModel

    # If init is already a datamodel, copy and return
    if isinstance(init, LigerIRISDataModel):
        if copy:
            return init.__class__(init, **kwargs)
        else:
            return init
    
    # Convert path to string
    if isinstance(init, Path):
        init = str(init)

    # Initialize variables used to select model class
    hdulist = {}
    file_name = None
    file_to_close = None

    # Get the encoding used with the filesystem error handler to
    # convert between Unicode filenames and bytes filenames
    if isinstance(init, bytes):
        init = init.decode(sys.getfilesystemencoding())
    
    # Pathlike object
    if isinstance(init, str) or hasattr(init, "read"):

        # Get just the filename no path
        file_name = os.path.basename(init)

        # File type
        file_type = filetype.check(init)

        # Load FITS or ASDF file
        if file_type == "fits":
            hdulist = fits.open(init, memmap=memmap)
            file_to_close = hdulist
        elif file_type == "asdf":
            asdffile = asdf.open(init, memmap=memmap)
            
            # Detect model type, then get defined model, and call it.
            model_class = class_from_model_type(asdffile)
            
            if model_class is None:
                # No model class found, so return generic model.
                warnings.warn(f"model_type not found with key 'DATAMODL'. Opening {file_name} as a LigerIRISDataModel")
                model = LigerIRISDataModel(asdffile, **kwargs)
            else:
                model = model_class(asdffile, **kwargs)

            return model

    elif isinstance(init, fits.HDUList):
        hdulist = init
    else:
        raise ValueError(f"Unsupported type for init: {type(init)}.")

    # If we have it, determine the shape from the science hdu
    if hdulist:
        # So we don't need to open the image twice
        init = hdulist
        info = init.fileinfo(0)
        if info is not None:
            file_name = info.get('filename')

    # First try to get the class name from the primary header
    model_class = class_from_model_type(hdulist)

    # Throw an error if these attempts were unsuccessful
    if model_class is None and file_to_close is not None:
        file_to_close.close()
    if model_class is None:
        raise TypeError("Can't determine datamodel class from argument to open")

    # Log a message about how the model was opened
    if file_name:
        log.debug(f'Opening {file_name} as {model_class}')
    else:
        log.debug(f'Opening as {model_class}')

    # Actually open the model
    try:
        model = model_class(init, **kwargs)
    except Exception:
        if file_to_close is not None:
            file_to_close.close()
        raise

    # Close the hdulist if we opened it
    if file_to_close is not None:
        # TODO: We need a better solution than messing with DataModel
        # internals.
        model._file_references.append(_FileReference(file_to_close))

    # Return the final model
    return model




def class_from_model_type(init):
    """
    Get the model type from the primary header, lookup to get class

    Parameters:
    init (HDUList | AsdfFile): The initializer.

    Returns:
    type | None: The LigerIRISDataModel class if found.
    """

    from . import DEFINED_MODELS
    if init:
        if isinstance(init, fits.hdu.hdulist.HDUList):
            primary = init[0]
            model_type = primary.header.get('DATAMODL')
        elif isinstance(init, asdf.AsdfFile):
            try:
                model_type = init.tree['meta']['model_type']
            except KeyError:
                model_type = None
        # Get the model type
        if model_type is None:
            model_class = None
        else:
            try:
                model_class = DEFINED_MODELS[model_type]
            except KeyError:
                model_class = None
    else:
        model_class = None

    # Return the class
    return model_class

