from pathlib import Path
from astropy.table import Table
from astropy.io import fits
from asdf import schema as asdf_schema
from stdatamodels import filetype
from stdatamodels.fits_support import from_fits_asdf, _fits_keyword_loader
from stdatamodels.model_base import _FileReference
from stdatamodels.schema import merge_property_trees
from stdatamodels import properties, validate
from stdatamodels import schema as mschema
from stpipe.datamodel import AbstractDataModel

import logging
logger = logging.getLogger(__name__)

def open(init, instrument_name : str | None = None, **kwargs):
    """
    Creates a DataModel from a number of different types.

    Parameters
    ----------
    init : str, astropy FITS HDUList, LigerIRISDataModel
        The input used to initialize the model. This can be:
        - A string representing a file path to a FITS or ASDF file.
        - An astropy FITS HDUList object.
        - An existing ASDF file object.
        - An existing `LigerIRISDataModel` instance. In this case, if ``copy`` is ``True``, a copy of the model will be returned, otherwise the same instance is returned. This is useful for functions that want to accept either a model or a filename.
    
    kwargs (dict): Additional arguments used to initialize the model.
        - **validate_arrays** (bool): If ``True``, arrays will be validated against ndim, max_ndim, and datatype validators in the schemas.
    
    Returns
    -------
    model : LigerIRISDataModel
        The specific LigerIRISDataModel instance.
    """

    # If init is already a DataModel, return it (or a copy)
    if isinstance(init, AbstractDataModel):
        return init
    
    # Convert path to string
    if isinstance(init, Path):
        init = str(init)

    # Get the model class from the input filename or HDUList
    if isinstance(init, str):
        logger.info(f"Opening file: {init}")
        with fits.open(init, memmap=True) as hdulist:
            model_class = get_model_type(hdulist)
            if instrument_name is None:
                instrument_name = get_instrument_name(hdulist)
    elif isinstance(init, fits.HDUList):
        if instrument_name is None:
            instrument_name = get_instrument_name(init)
        model_class = get_model_type(init)

    # Initialize the model
    model = model_class(init, instrument_name=instrument_name, **kwargs)

    return model

def get_model_type(input : str | fits.HDUList):
    """
    Determines the Python DataModel class from either a FITS filename or an HDUList.
    
    Parameters
    ----------
    input : str or fits.HDUList
        Either a FITS filename path or an already-opened HDUList object.
        The DATAMODL keyword will be read from the primary header.
    
    Returns
    -------
    model_type : type[LigerIRISDataModel]
        The LigerIRISDataModel class.
    
    Raises
    ------
    TypeError
        If input is neither a string nor an HDUList.
    ValueError
        If the model name is not found in DEFINED_MODELS, or if no DATAMODL 
        keyword is found in the header.
    """
    from . import DEFINED_MODELS
    
    # Open the file or use the provided HDUList
    if isinstance(input, str):
        with fits.open(input, memmap=True) as hdulist:
            model_name = hdulist[0].header.get('DATAMODL')
    elif isinstance(input, fits.HDUList):
        model_name = input[0].header.get('DATAMODL')
    else:
        raise TypeError(
            f"input must be a string (filename) or fits.HDUList, got {type(input).__name__}"
        )
    
    # Check if DATAMODL keyword was found
    if model_name is None:
        raise ValueError("No DATAMODL key found in FITS header")
    
    # Look up the model type
    model_type = DEFINED_MODELS.get(model_name, None)
    if model_type is None:
        raise ValueError(f"Model type '{model_name}' not found in DEFINED_MODELS.")
    
    return model_type

def get_instrument_name(input : str | fits.HDUList):
    """
    Get the instrument name from either a FITS filename or an HDUList.
    
    Parameters
    ----------
    input : str or fits.HDUList
        Either a FITS filename path or an already-opened HDUList object.
        The INSTRUME keyword will be read from the primary header.
    
    Returns
    -------
    instrument_name : str
        The instrument name if found.
    
    Raises
    ------
    TypeError
        If input is neither a string nor an HDUList.
    ValueError
        If no INSTRUME keyword is found in the header.
    """
    
    # Open the file or use the provided HDUList
    if isinstance(input, str):
        with fits.open(input, memmap=True) as hdulist:
            instrument_name = hdulist[0].header.get('INSTRUME')
    elif isinstance(input, fits.HDUList):
        instrument_name = input[0].header.get('INSTRUME')
    else:
        raise TypeError(
            f"input must be a string (filename) or fits.HDUList, got {type(input).__name__}"
        )
    
    # Check if INSTRUME keyword was found
    if instrument_name is None:
        raise ValueError("No INSTRUME key found in FITS header")
    
    return instrument_name

def get_instrument_config(input : str | fits.HDUList | None = None, instrument_name : str | None = None):
    """
    Get the instrument configuration class from either a FITS filename or an HDUList.
    
    Parameters
    ----------
    input : str or fits.HDUList, optional
        Either a FITS filename path or an already-opened HDUList object.
        The INSTRUME keyword will be read from the primary header.
    instrument_name : str, optional
        The instrument name. If provided, this will be used instead of reading the instrument name from the FITS header.
    
    Returns
    -------
    config_class : type
        The instrument config class if found.
    
    Raises
    ------
    TypeError
        If input is neither a string nor an HDUList.
    ValueError
        If no INSTRUME keyword is found in the header, or if the instrument
        config is not found in INSTRUMENT_CONFIGS.
    """
    from . import INSTRUMENT_CONFIGS

    if instrument_name is None:
        assert input is not None, "Either input or instrument_name must be provided."
        instrument_name = get_instrument_name(input)
    
    config_class = INSTRUMENT_CONFIGS.get(instrument_name, None)
    if config_class is None:
        raise ValueError(f"Instrument config for '{instrument_name}' not found.")
    
    return config_class

_DEFAULT_SCHEMA = {
    "properties": {
        "meta": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                },
                "model_type": {
                    "type": "string",
                },
            },
        },
    },
}

def get_schema(input=None, model_class: type['LigerIRISDataModel'] | None = None, instrument_name: str | None = None) -> dict:
    """
    Build the full schema for a DataModel with instrument-specific overrides.
    
    The schema is constructed by applying modifications in this order:
    1. Base model schema (e.g., ImagerModel.schema)
    2. Instrument-wide modifications (e.g., LigerModifications.schema)
    3. Instrument + Model-specific modifications (e.g., LigerImagerModelModifications.schema)
    
    Parameters
    ----------
    model_class : Type[LigerIRISDataModel] | None
        The DataModel class (e.g., ImagerModel). If None, it will be determined from the input file header.
    instrument_name : str | None
        Instrument name ('Liger' or 'IRIS'). If None, it will be determined from the input file header.
        
    Returns
    -------
    schema : dict
        The fully constructed schema with all overrides applied.
        
    Raises
    ------
    ValueError
        If instrument is not recognized or model_class has no schema_url.
        
    Examples
    --------
    >>> schema = get_schema(model_class=ImagerModel, instrument_name='Liger')
    >>> schema = get_schema(model_class=DarkModel, 'IRIS')
    """

    if instrument_name is None and input is not None:
        instrument_name = get_instrument_name(input)

    if model_class is None and isinstance(input, type):
        model_class = input
    elif model_class is None and input is not None:
        model_class = get_model_type(input)
    
    # Load the base model schema if it exists
    if hasattr(model_class, 'schema_url') and model_class.schema_url is not None:
        base_schema = asdf_schema.load_schema(
            model_class.schema_url,
            resolve_references=True
        )
    else:
        base_schema = _DEFAULT_SCHEMA
    
    # Build allOf chain with base + modifications
    allof_schemas = [base_schema]
    
    # Add instrument-wide modifications if they exist
    instrument_mod_url = f"https://oirlab.github.io/schemas/{instrument_name.lower()}_core.schema"
    try:
        instrument_mods = asdf_schema.load_schema(
            instrument_mod_url,
            resolve_references=True
        )
        allof_schemas.append(instrument_mods)
    except Exception:
        # Instrument modifications are optional
        pass
    
    # Add instrument + model-specific modifications if they exist
    specific_mod_url = f"https://oirlab.github.io/schemas/{instrument_name.lower()}{model_class.__name__}.schema"
    try:
        specific_mods = asdf_schema.load_schema(
            specific_mod_url,
            resolve_references=True
        )
        allof_schemas.append(specific_mods)
    except Exception:
        # Model-specific modifications are optional
        pass
    
    # Combine all schemas using allOf
    if len(allof_schemas) == 1:
        # No modifications, just return base
        #return allof_schemas
        return merge_property_trees(base_schema)
    else:
        # Create a schema with allOf combiner and merge
        combined_schema = {"allOf": allof_schemas}
        return merge_property_trees(combined_schema)
    
def get_receipt_table(input) -> Table:
    """
    Get the receipt table from either a DataModel, FITS HDUList, or filename.
    Reads the "RECEIPT" extension from the FITS file and returns it as an Astropy Table.

    Parameters
    ----------
    input : LigerIRISDataModel, fits.HDUList, or str
        The input from which to extract the receipt table.
    
    Returns
    -------
    receipt_table : astropy.table.Table
    """
    if isinstance(input, AbstractDataModel):
        return input.receipt_table
    elif isinstance(input, fits.HDUList):
        return Table(input['RECEIPT'])
    elif isinstance(input, str):
        with fits.open(input, memmap=True) as hdulist:
            return Table(hdulist['RECEIPT'])
    else:
        raise TypeError(
            f"input must be a LigerIRISDataModel, fits.HDUList, or str, got {type(input).__name__}"
        )

def get_meta(input : str | fits.HDUList | AbstractDataModel, properties : dict | None = None) -> dict:
    """

    Parameters
    ----------
    input : str, fits.HDUList, or AbstractDataModel
        The input from which to extract metadata. This can be a filename, an already-opened HDUList, or a DataModel instance.

    properties : dict, optional
        A dictionary specifying which metadata properties to extract. The keys should be the full property paths (e.g., "meta.instrument.filter"). If None, all properties in the schema with a "fits_keyword" will be extracted.

    Returns
    -------
    dict
        Metadata dictionary, nested according to the schema structure.
    
    """
    if isinstance(input, str):
        with fits.open(input, memmap=True) as hdulist:
            instrument_name = get_instrument_name(hdulist)
            model_class = get_model_type(hdulist)
            schema = get_schema(model_class=model_class, instrument_name=instrument_name)
            return _get_meta_from_hdulist(hdulist, schema, properties)
    elif isinstance(input, fits.HDUList):
        instrument_name = get_instrument_name(input)
        model_class = get_model_type(input)
        schema = get_schema(model_class=model_class, instrument_name=instrument_name)
        return _get_meta_from_hdulist(input, schema, properties)
    elif isinstance(input, AbstractDataModel):
        with fits.open(input._filepath, memmap=True) as hdulist:
            return _get_meta_from_hdulist(hdulist, input._schema, properties)
    else:
        raise TypeError(
            f"input must be a str, fits.HDUList, or AbstractDataModel, got {type(input).__name__}"
        )

def _get_meta_from_hdulist(
    hdulist : fits.HDUList,
    schema : dict,
    properties : dict | None = None,
) -> dict:

    known_keywords = {}
    hdu_cache = {}

    meta_dict = {}
    hdu_index = 0

    def callback(schema, path, combiner, ctx, recurse):
        if len(path) == 0 or path[0] != 'meta':
            return
        prop = '.'.join(path)
        if properties is not None and prop not in properties:
            return
        if "fits_keyword" not in schema:
            return

        fits_keyword = schema["fits_keyword"]
        
        fits_val = _fits_keyword_loader(
            hdulist,
            fits_keyword,
            schema,
            hdu_index,
            known_keywords,
            hdu_cache
        )
        meta_dict[prop] = fits_val

    # Walk the schema and extract metadata
    mschema.walk_schema(schema, callback)

    return meta_dict


def walk_schema_values(model, meta_only=False):
    schema = model._schema
    if meta_only:
        schema = schema.get("properties", {}).get("meta", {})
        base_path = ["meta"]
        root = model.meta
    else:
        base_path = []
        root = model

    def resolve(path):
        obj = root
        for key in path[len(base_path):]:
            if obj is None or not hasattr(obj, key):
                return None
            obj = getattr(obj, key)
        return obj

    def recurse(subschema, path, combiner):
        if subschema.get("type") != "object":
            yield path, subschema, resolve(path)

        for c in ("allOf", "not"):
            for sub in subschema.get(c, []):
                yield from recurse(sub, path, c)

        for c in ("anyOf", "oneOf"):
            for sub in subschema.get(c, []):
                yield from recurse(sub, path + [c], c)

        if subschema.get("type") == "object":
            for key, val in subschema.get("properties", {}).items():
                yield from recurse(val, path + [key], combiner)

        if subschema.get("type") == "array":
            items = subschema.get("items", {})
            if isinstance(items, list):
                for item in items:
                    yield from recurse(item, path + ["items"], combiner)
            elif items:
                yield from recurse(items, path + ["items"], combiner)

    yield from recurse(schema, base_path, None)
    del recurse
