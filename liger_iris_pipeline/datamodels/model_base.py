import os
from typing import ClassVar, Sequence

from astropy.time import Time
import numpy as np
from astropy.io import fits
from astropy.table import Table
from datetime import datetime
from asdf import AsdfFile
from stdatamodels.model_base import DataModel, _FileReference
from stdatamodels import fits_support, properties
from stdatamodels.util import get_envar_as_boolean
from stdatamodels.validate import ValidationWarning
from stdatamodels.properties import ObjectNode
from jwst.model_blender import blendmodels

from .utils import get_instrument_name, get_schema, get_meta, get_instrument_config, walk_schema_values
from .utils import open as datamodel_open
from .._version import __version__
from .meta_utils import set_default_exposure_meta, set_default_target_meta, set_full_subarray_meta, set_default_imager_wcs_meta, set_default_ifs_wcs_meta, get_semester_id, update_model_meta
from ..utils.endian_utils import convert_endianness

from koa_middleware.utils import get_env_var_bool
from .liger_config import LigerConfig, _set_koa_meta
#from .iris_config import IRISConfig

from uuid import uuid4 as make_uuid4
import warnings
import logging
logger = logging.getLogger(__name__)

from .mixins import DefaultReceiptTableMixin, DefaultCalibrationsTableMixin

__all__ = ["LigerIRISDataModel", "CalibrationModel"]


class LigerIRISDataModel(DefaultReceiptTableMixin, DefaultCalibrationsTableMixin, DataModel):
    """
    The base data model for Liger and IRIS data products.
    This class should not be instantiated on its own.
    """

    _DEFAULT_INSTRUMENT = 'Liger'

    # TODO: Move this to config classes
    _DETECTOR_SIZES : ClassVar[dict[str, tuple[int, int]]] = {
        'Liger' : {
            'IMG' : (2048, 2112),
            'IFS' : (4096, 4196),
        },
        'IRIS' : {
            'IMG' : (4096, 4196),
            'IFS' : (4096, 4196),
        }
    }

    def __init__(
        self,
        init=None,
        schema : dict | None = None,
        pass_invalid_values : bool | None = None,
        strict_validation : bool | None = None,
        validate_on_assignment : bool | None = None,
        validate_arrays : bool = False,
        ignore_missing_extensions : bool = True,
        ignore_unrecognized_tag : bool = False,
        instrument_name : str | None = None,
        config : type | None = None,
        no_asdf_extension : bool = False,
        meta_only : bool = False,
        meta : dict | None = None,
        **kwargs,
    ):
        """
        Initialize a data model.

        Parameters
        ----------
        init : str, tuple, astropy FITS HDUList, ndarray, dict, or None
            Initialization source for the data model. Can be:
                - None: Create a default data model with no shape.
                - str (file path): Initialize from the given file (FITS or ASDF).
                - readable file object: Initialize from the given file object.
                - astropy FITS HDUList: Initialize from the given HDUList.
                - ndarray: Used to initialize the data array.
                - dict: The object model tree for the data model.
                - datamodel: Initialize from an existing DataModel instance (shallow copy, converts between model subtypes if schemas are compatible).

        schema : dict or str, optional
            Tree of objects representing a JSON schema, or string naming a schema. If not provided, the schema associated with this class will be used.
        pass_invalid_values : bool or None, optional
            If True, values that do not validate the schema will be added to the metadata. If False, they will be set to None. If None, value will be taken from the environmental PASS_INVALID_VALUES. Default is False.
        strict_validation : bool or None, optional
            If True, schema validation errors will generate an exception. If False, they will generate a warning. If None, value will be taken from the environmental STRICT_VALIDATION. Default is False.
        validate_on_assignment : bool or None, optional
            If None, value will be taken from the environmental VALIDATE_ON_ASSIGNMENT, defaulting to True if no environment variable is set. If True, attribute assignments are validated at the time of assignment. Validation errors generate warnings and values will be set to None. If False, schema validation occurs only once at the time of write. Validation errors generate warnings.
        validate_arrays : bool, optional
            If True, arrays will be validated against ndim, max_ndim, and datatype validators in the schemas.
        ignore_missing_extensions : bool, optional
            When False, raise warnings when a file is read that contains metadata about extensions that are not available. Defaults to True.
        ignore_unrecognized_tag : bool, optional
            When False, raise warnings when an unrecognized tag is encountered. When True, ignore unrecognized tags.
        instrument_name : str or None
            The instrument name to use for schema selection.
        meta_only : bool, optional
            If True, explicitly load only the metadata only. Defaults to False.
        meta : dict or None, optional
            A dictionary of existing metadata. Keys can start with 'meta' or a meta attribute name. For example, ``meta.instrument.filter`` or ``instrument.filter``.
        kwargs
            Additional keyword arguments are expected to be array-like attributes of the data model. These will be initialized with the given values only if they are defined in the schema and the schema expects an array-like value. Kwargs are only allowed when ``init`` is None, a tuple, or a numpy array.

        Notes
        -----
        This overrides DataModel.__init__ to first determine the instrument_name
        to select the appropriate schema for the data model.

        Examples
        --------
        >>> model = ImageModel(data=np.ones((10, 10)), dq=np.zeros((10, 10)))  # doctest: +SKIP
        """

        # Determine instrument name from inputs
        if isinstance(instrument_name, str):
            # Directly passed
            pass
        if isinstance(meta, dict) and 'instrument.name' in meta:
            # From meta dict with 'instrument.name' key
            instrument_name = meta['instrument.name']
        elif isinstance(meta, ObjectNode):
            # From meta ObjectNode with instrument.name attribute
            instrument_name = meta.instrument.name
        elif config is not None:
            # From config class
            instrument_name = config.instrument_name
        elif isinstance(init, (str, fits.hdu.hdulist.HDUList)):
            # From filename or HDUList
            instrument_name = get_instrument_name(init)
        else:
            # From environment variable or default
            instrument_name = os.environ.get('LIGER_IRIS_DRP_INSTRUMENT_NAME', self._DEFAULT_INSTRUMENT)

        # Get instrument config class from instrument name
        if config is not None:
            self._config = config
        else:
            self._config = get_instrument_config(init, instrument_name=instrument_name)
        assert self._config is not None, "Could not determine instrument config class."
        assert self._config.instrument_name == instrument_name, "Instrument name mismatch."

        # Get the schema from the instrument name
        if schema is None:
            schema = self.get_schema(instrument_name)

        super().__init__(
            init=init,
            schema=schema,
            pass_invalid_values=pass_invalid_values,
            strict_validation=strict_validation,
            validate_on_assignment=validate_on_assignment,
            validate_arrays=validate_arrays,
            ignore_missing_extensions=ignore_missing_extensions,
            ignore_unrecognized_tag=ignore_unrecognized_tag,
            **kwargs,
        )

        # Sets meta.instrument.name
        self.instrument_name = instrument_name

        # Initialize metadata
        # NOTE: This may change depending on DataModel.from_datamodels()
        if isinstance(meta, dict):
            update_model_meta(self, **meta)
        elif isinstance(meta, ObjectNode):
            self.meta = meta

        # Call on_init again. Need to find a better solution moving forward.
        self.on_init(init)

        # Call config set_defaults after on_init
        # NOTE: Ordering of default metadata setting may change
        self._config.set_defaults(self)

    @classmethod
    def get_schema(cls, instrument_name : str) -> dict:
        """
        Retrieve the schema for the given DataModel and instrument name.

        Returns
        -------
        schema : dict
            The merged schema dictionary for this DataModel and instrument name.
        """
        return get_schema(cls, instrument_name=instrument_name)

    def __setattr__(self, attr, value):
        """
        Override DataModel.__setattr__ to allow setting instrument_name property.

        Parameters
        ----------
        attr : str
            The attribute name to set.
        value : Any
            The value to set the attribute to.
        """
        if attr in frozenset(("shape", "history", "_extra_fits", "schema", "instrument_name", "_config")):
            object.__setattr__(self, attr, value)
        else:
            super().__setattr__(attr, value)

    @property
    def instrument_name(self):
        """
        Returns the instrument name. Alias for ``meta.instrument.name``.
        """
        return self.meta.instrument.name
    
    @instrument_name.setter
    def instrument_name(self, instrument_name : str):
        self.meta.instrument.name = instrument_name

    def on_init(self, init):
        """
        Hook invoked by the base class before returning a newly created model instance.
        The base implementation sets common metadata values.
        
        Parameters
        ----------
        init
            The input initializer. See DataModel.__init__ for valid types.
        """
        # Set the filepath and filename
        if isinstance(init, str):
            self._filepath = os.path.abspath(init)
            self.meta.filename = os.path.basename(self._filepath)
        elif isinstance(init, fits.hdu.hdulist.HDUList):
            self._filepath = os.path.abspath(init.filename())
            self.meta.filename = os.path.basename(self._filepath)
        else:
            self._filepath = None
            self.meta.filename = None

        # Set the model type
        self.meta.model_type = self.__class__.__name__

        # DRS version
        if self.meta.drp_version is None:
            self.meta.drp_version = __version__

        # Datetime
        if self.meta.datetime_obs is None:
            if self.meta.exposure.mjd_start is None:
                # NOTE: Useful for development only, this is dangerous!
                self.meta.datetime_obs = Time.now().isot
            else:
                self.meta.datetime_obs = Time(self.meta.exposure.mjd_start, format='mjd').isot

        # Semester ID
        if self.meta.program.semester_id is None and self.meta.datetime_obs is not None:
            self.meta.program.semester_id = get_semester_id(self.meta.datetime_obs)

        # Initialize all metadata with defaults.
        from .utils import walk_schema_values
        for path, sub_schema, val in walk_schema_values(self, meta_only=True):
            if sub_schema.get('default') is not None and val is None:
                path = '.'.join(path)
                update_model_meta(self, **{path: sub_schema['default']})

        set_default_exposure_meta(self)
        set_default_target_meta(self)
        if self.instrument_name == 'IRIS':
            set_full_subarray_meta(self)

        # Convert any None values that have enums to 'N/A' string.
        #self.fix_enum_none()

        # Array endianness
        for attr in self.get_data_names():
            data = getattr(self, attr)
            if (
                data is not None
                and isinstance(data, np.ndarray)
                and (np.issubdtype(data.dtype, np.number) or np.issubdtype(data.dtype, np.bool_))
                and 0 not in data.shape
            ):
                setattr(self, attr, convert_endianness(data))

        super().on_init(init)

    def get_data_names(self) -> list[str]:
        """
        Returns the names of all top level attributes, ignoring meta.

        Returns
        -------
        list[str]
            The names of all data attributes in the model.
        """
        return [k for k in self._schema['properties'] if k != 'meta']

    def _set_defaults(self):
        """
        Subclass hook for setting default metadata values.
        This method is called by `set_defaults` and can be overridden by subclasses to set additional default metadata.
        """
        pass
        
    def on_save(self, filepath : str | None = None):
        """
        Hook invoked by the base class before writing a model to a file (FITS or ASDF).
        
        This method updates version, creation date, filename, and model type metadata.
        """
        self.meta.drp_version = __version__
        self.meta.model_type = self.__class__.__name__
        if filepath is not None:
            self._filepath = os.path.abspath(filepath)
            self.meta.filename = os.path.basename(self._filepath)
        if self.meta.last_processed is None:
            self.meta.last_processed = datetime.now().isoformat(timespec="milliseconds")

        if self.meta.instrument.name == 'Liger':
            _set_koa_meta(self)

    @property
    def crds_observatory(self):
        """
        NOTE: This method is necessary so that we subtype AbstractDataModel from stpipe.
        """
        return None
    
    def get_crds_parameters(self):
        """
        NOTE: This method is necessary so that we subtype AbstractDataModel from stpipe.
        """
        return {}
    
    @staticmethod
    def _generate_filename(
        instrument_name : str,
        semester_id : str | None,
        program_id : str | None,
        obs_number : str | None,
        detector : str, level : str = '0',
        exp_num : int | str = '0001', exp_type : str = 'SCI', subarray_id : int | str | None = None,
        suffix : str | None = None
    ) -> str:
        """
        Generates a filename.

        Parameters
        ----------
        instrument_name : str
            The instrument name.
        semester_id : str or None
            The semester ID. Defaults to None.
        program_id : str or None
            The program number. Defaults to None.
        obs_number : str or None
            The observation number. Defaults to None.
        detector : str
            The detector name.
        level : str
            The data level.
        exp_num : int or str, optional
            The exposure number. Defaults to '0001'.
        exp_type : str, optional
            The exposure type. Defaults to 'SCI'.
        subarray_id : int or str or None, optional
            The subarray ID. Defaults to None for IRIS. Liger does not use subarrays.
        suffix : str or None, optional
            Suffix to append to the filename. Defaults to None.

        Returns
        -------
        str
            The generated filename.
        """
        if semester_id is None:
            semester_id = get_semester_id(Time.now().isot)
        if program_id is None:
           program_id = 'P001'
        if obs_number is None:
            obs_number = '001'
        if instrument_name.lower() == 'iris':
            instrument_name = 'IRIS'
        elif instrument_name.lower() == 'liger':
            instrument_name = 'Liger'
        else:
            raise ValueError(f"Unknown instrument {instrument_name}")
        if isinstance(exp_num, int):
            exp_num = str(exp_num).zfill(4)
        if isinstance(subarray_id, (int, str)):
            subarray_id = '-' + str(subarray_id).zfill(2)
        else:
            if instrument_name.lower() == 'iris':
                subarray_id = '-00'
            else:
                subarray_id = ''
        if suffix is None:
            suffix = ''
        else:
            suffix = '_' + suffix
        return f"{instrument_name}_{semester_id}_{program_id}-{obs_number}_{detector.upper()}_{exp_type}{int(level)}_{exp_num}{subarray_id}{suffix}.fits"
    
    def generate_filename(self, suffix : str | None = None) -> str:
        """
        Generates a filename for this model instance.

        Format:
            {instrument_name}_{semester_id}_{program_id}-{obs_number}_{detector.upper()}_{exp_type}{int(level)}_{exp_num}{subarray_id}{suffix}.fits

        Examples
        --------
        - 

        Parameters
        ----------
        suffix : str or None, optional
            Suffix to append to the filename. Defaults to None.

        Returns
        -------
        str
            The generated filename.
        """
        filename = self._generate_filename(
            instrument_name=self.meta.instrument.name,
            semester_id=self.meta.program.semester_id,
            program_id=self.meta.program.program_id,
            obs_number=self.meta.program.observation_number,
            detector=self.meta.instrument.detector,
            exp_type=self.meta.exposure.type,
            level=self.meta.data_level,
            exp_num=self.meta.exposure.exposure_number,
            subarray_id=self.meta.subarray.id, suffix=suffix
        )
        
        # Set new filename
        self.meta.filename = filename

        # Set new filepath if input dir already exists.
        # NOTE: This behavior might change in the future.
        if self._filepath is not None:
            input_dir = os.path.dirname(os.path.abspath(self._filepath))
            self._filepath = os.path.join(input_dir, self.meta.filename)

        return self.meta.filename

    def get_primary_array_name(self) -> str:
        return 'data'

    def save(
        self,
        output_path : str | None = None,
        filename : str | None = None,
        output_dir : str | None = None,
        suffix : str | None = None,
        overwrite : bool = True,
        **kwargs
    ) -> str:
        """
        Save the model to a file.

        Parameters
        ----------
        output_path : str or None, optional
            The output path to save to. Defaults to self._filepath.
        filename : str or None, optional
            The filename to save to. Defaults to None.
        output_dir : str or None, optional
            The directory to save to. Defaults to the directory of self._filepath, then os.getcwd().
        suffix : str or None, optional
            The suffix to add to the filename. Defaults to None.
        **kwargs
            Additional arguments passed to ``HDUList.writeto()``.

        Returns
        -------
        str
            The absolute path to the saved file.
        """
        if output_path is not None:
            filepath = os.path.abspath(output_path)
        elif output_dir is not None and filename is not None:
            filepath = os.path.join(output_dir, filename)
        elif output_dir is not None and filename is None:
            filename = self.generate_filename(suffix=suffix)
            filepath = os.path.abspath(os.path.join(output_dir, filename))
        elif output_dir is None and filename is not None:
            filepath = os.path.abspath(os.path.join(os.getcwd(), filename))
        else:
            filename = self.generate_filename(suffix=suffix)
            filepath = os.path.abspath(os.path.join(os.getcwd(), filename))
        self.to_fits(filepath, **(kwargs | {'overwrite' : overwrite}))
        return filepath
    
    def to_fits(self, init, *args, **kwargs):
        """
        Write a data model to a FITS file.

        Parameters
        ----------
        init : file path or file object
            The file to write to.
        args
            Additional positional arguments passed to astropy.io.fits.writeto.
        kwargs
            Additional keyword arguments passed to astropy.io.fits.writeto.

        Notes
        -----
        This method overrides DataModel.to_fits so that the receipt extension is at the end.
        """
        self.on_save(init)
        hdulist = fits_support.to_fits(self._instance, self._schema)
        if 'RECEIPT' in hdulist:
            receipt = hdulist['RECEIPT']
            hdulist.remove(receipt)
            hdulist.append(receipt)
        if 'CALIBRATIONS' in hdulist:
            calibrations = hdulist['CALIBRATIONS']
            hdulist.remove(calibrations)
            hdulist.append(calibrations)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Card is too long")
            if self._no_asdf_extension:
                # For some old files that were written out before the
                # _no_asdf_extension existed, these will have an ASDF
                # extension, which may get passed along through extra_fits.
                # Avoid this.
                if "ASDF" in hdulist:
                    del hdulist["ASDF"]
            hdulist.writeto(init, *args, **kwargs)

    @property
    def shape(self):
        """
        Return the shape of the primary array.

        Notes
        -----
        In the parent class, this property is cached after the first call.
        Here, the shape is always updated so users can manipulate data arrays after instantiating the model.
        """
        primary_array_name = self.get_primary_array_name()
        if primary_array_name and self.hasattr(primary_array_name):
            primary_array = getattr(self, primary_array_name)
            if primary_array is not None:
                self._shape = primary_array.shape
            else:
                self._shape = self.get_default_shape()
        return self._shape
    
    def get_default_shape(self):
        """
        Get the default shape of the primary array.

        Notes
        -----
        This is a fallback method that uses ``instrument_name`` and ``instrument.detector``.
        This pattern still allows for DataModels to use any shape.

        Returns
        -------
        tuple[int, int]
            The default shape of the primary array.
        """
        return self._DETECTOR_SIZES[self.instrument_name][self.meta.instrument.detector]
    
    def copy(self, memo=None):
        """
        Return a deep copy of this model.

        Notes
        -----
        This overrides DataModel.copy to pass the instrument_name to the copied model.

        Parameters
        ----------
        memo : dict, optional
            A dictionary to use as a memoization table for deep copy.
        """
        result = self.__class__(
            init=None,
            pass_invalid_values=self._pass_invalid_values,
            strict_validation=self._strict_validation,
            instrument_name=self.instrument_name,
        )
        self.clone(result, self, deepcopy=True, memo=memo)
        return result
    
    def append_receipts(self, other : DataModel | str | list | dict):
        """
        Append the receipts from a group of data models to this model's receipt.

        Parameters
        ----------
        other : DataModel, str, list, or dict
            A single data model, filepath, list of data models/filepaths, or dict of data models/filepaths.
        """
        if isinstance(other, (DataModel, str)):
            other = [other]
        elif isinstance(other, dict):
            other = list(other.values())
        elif isinstance(other, list):
            other = other
        else:
            raise ValueError("Invalid type for other")
        for _other in other:
            model = datamodel_open(_other)
            self.receipt = np.concatenate((self.receipt, model.receipt))

    def append_calibrations(self, other : DataModel | list[DataModel] | dict[DataModel]) -> None:
        """
        Append calibrations from another model to this model.

        Parameters
        ----------
        other : LigerIRISDataModel, list, or dict.
            All "other" models calibrations tables will be appended to the "input's" calibrations table.
        """
        if isinstance(other, DataModel):
            other = [other]
        elif isinstance(other, dict):
            other = list(other.values())
        elif isinstance(other, list):
            other = other
        else:
            raise ValueError("Invalid type for other")
        for _other in other:
            model = datamodel_open(_other)
            self.calibrations = np.concatenate((self.calibrations, model.calibrations))
    
    @classmethod
    def from_datamodels(
        cls,
        input,
        append_receipts : bool = True,
        append_calibrations : bool = True,
        include_data : bool = False,
        **kwargs
    ) -> DataModel:
        """
        Create a new data model from the context of a group of data models.

        Parameters
        ----------
        input : DataModel, str, list, or dict
            A single data model, filepath, list of data models/filepaths, or dict of data models/filepaths.
        append_receipts : bool, optional
            If True, the receipt tables of the input models will be appended together in the output model.
            Default is True.
        append_calibrations : bool, optional
            If True, the calibrations tables of the input models will be appended together in the output model.
            Default is True.
        include_data : bool, optional
            If True, the data arrays and tables of the first input model will be included in the output model (ignoring HDRTAB, RECEIPT, CALIBRATIONS). Default is False.
        **kwargs
            Additional keyword arguments passed to the data model constructor.
        """
        
        # Normalize to iterable
        if input is None:
            raise ValueError("No models provided")
        elif isinstance(input, (str, LigerIRISDataModel)):
            input = [input]
        elif isinstance(input, dict):
            input = list(input.values())
        
        if not isinstance(input, Sequence):
            raise ValueError("Input must be a DataModel, filepath, list of DataModels/filepaths, or dict of DataModels/filepaths.")

        # Create new model
        first_model = datamodel_open(input[0], meta_only=True)
        #instrument_name = first_model.instrument_name
        output_model = cls(
            config=first_model._config,
            pass_invalid_values=first_model._pass_invalid_values,
            strict_validation=first_model._strict_validation,
            validate_on_assignment=first_model._validate_on_assignment,
            validate_arrays=first_model._validate_arrays,
            no_asdf_extension=first_model._no_asdf_extension,
            **kwargs
        )

        # Blend the metadata
        input_models = [datamodel_open(m, meta_only=True) for m in input]
        blendmodels(output_model, input_models)
        output_model._filepath = None
        output_model.meta.filename = None

        # Forward data?
        if include_data:
            assert len(input) == 1, "Cannot include data when merging multiple models. Set include_data=False or provide a single model."
            first_model = datamodel_open(input[0])
            #for extname in model_out.EXTENSIONS:
            for attr in output_model.get_data_names():
                if attr in ('calibrations', 'receipt'):
                    continue
                if first_model.hasattr(attr):
                    setattr(output_model, attr, getattr(first_model, attr, None))

        # Merge tables
        for _input in input:

            input_model = datamodel_open(_input)

            if append_receipts:
                output_model.append_receipts(input_model)

            if append_calibrations:
                output_model.append_calibrations(input_model)

        return output_model
    
    def __repr__(self):
        """
        Return a string representation of the model.

        Notes
        -----
        This overrides DataModel.__repr__ to include the instrument name at the front.
        """
        buf = ["<"]
        if self.instrument_name is not None:
            buf.append(self.instrument_name)
            buf.append(" ")
        buf.append(self._model_type)

        if self.shape:
            buf.append(str(self.shape))

        try:
            filename = self.meta.filename
        except AttributeError:
            filename = None
        if filename:
            buf.append(" from ")
            buf.append(filename)
        buf.append(">")

        return "".join(buf)

    @property
    def receipt_table(self):
        """
        Returns the receipt attribute as an Astropy Table.
        """
        if self.hasattr('receipt') and self.receipt is not None:
            return Table(self.receipt)
        
    @property
    def calibrations_table(self):
        """
        Returns the calibrations attribute as an Astropy Table.
        """
        if self.hasattr('calibrations') and self.calibrations is not None:
            return Table(self.calibrations)
        
    @property
    def hdrtab_table(self):
        """
        Returns the hdrtab attribute as an Astropy Table.
        """
        if self.hasattr('hdrtab') and self.hdrtab is not None:
            return Table(self.hdrtab)

    @property
    def instance(self) -> dict:
        """
        Returns the internal instance tree (dict), at self._instance.
        """
        return self._instance
    
    def to_record(self) -> dict:
        """
        Convert the metadata to a dictionary record.

        Returns
        -------
        record : dict
            The metadata as a dictionary.
        """
        from .utils import walk_schema_values
        record = {}
        for path, sub_schema, val in walk_schema_values(self, meta_only=True):
            cal_db = sub_schema.get('cal_db', False)
            if cal_db is True:
                record['.'.join(path[1:])] = val
            elif isinstance(cal_db, str):
                record[cal_db] = val
        return record
    
    def fix_enum_none(self, value='N/A'):
        """
        For all metadata entries with an enum and a current value of None, set to 'None'.
        """
        from .utils import walk_schema_values
        for path, sub_schema, val in walk_schema_values(self, meta_only=True):
            if 'enum' in sub_schema and val is None:
                enum = sub_schema['enum']
                if value in enum:
                    obj = self
                    for key in path[:-1]:
                        try:
                            obj = getattr(obj, key)
                        except:
                            # Excepttion for listnode types
                            # Eventually add explicit check, remove this try/except
                            pass
                    setattr(obj, path[-1], value)
                    
    


class CalibrationModel(LigerIRISDataModel):
    """
    A base data model for Liger and IRIS calibrations.
    Subclasses should define the ``_cal_type`` attribute to identify the calibration type.
    """

    _cal_type = None

    def on_init(self, init):
        super().on_init(init)
        self.meta.cal_type = self._cal_type
        if self.meta.cal_id is None:
            self.generate_calibration_id()
        if self.meta.target.name is None:
            self.meta.target.name = self._cal_type

    def print_err(self, message):
        if self._strict_validation:
            raise ValueError(message)
        else:
            warnings.warn(message, ValidationWarning)


    @staticmethod
    def _generate_filename(
        instrument_name : str,
        datetime_obs : str,
        detector : str,
        cal_type : str,
        master_cal : bool = False,
        cal_version : str | None = None,
        origin : str | None = None,
        suffix : str | None = None,
    ):
        """
        Generate a filename for the calibration file.

        Format:
            {instrument}_{datetime_obs}_{mode}_{cal_type}_{cal_version}_{suffix}.fits

        Examples
        --------
        


        Parameters
        ----------
        instrument_name : str
            The instrument name.
        datetime_obs : str
            The observation datetime in ISO format.
        detector : str
            The detector name (IMG, IMG1-4, IFS)
        cal_type : str
            The calibration type (e.g. 'dark', 'detflat').
        master_cal : bool, optional
            Whether this is a master calibration file. Defaults to False.
        cal_version : str or None, optional
            The calibration version. Defaults to None, which will omit the version from the filename.
        """
        
        # Resolve instrument name
        if instrument_name.lower() == 'iris':
            instrument = 'IRIS'
        elif instrument_name.lower() == 'liger':
            instrument = 'Liger'
        else:
            raise ValueError(f"Unknown instrument {instrument}")
        
        # Strings for master and origin
        if master_cal:
            cal_type = f"mastercal-{cal_type}"
        else:
            cal_type = f"cal-{cal_type}"

        # Date time string
        datetime_str = datetime_obs.replace('-', '').replace(':', '').replace('T', '').split('.')[0]

        # Construct starting filename
        filename = f"{instrument_name}_{datetime_str}_{detector}_{cal_type}"

        # Version
        if cal_version is not None:
            if isinstance(origin, str) and origin.lower() == 'local':
                cal_version = f"{cal_version}-local"
            filename = f"{filename}_{cal_version}"
        
        # Add suffix
        if suffix is not None:
            filename = f"{filename}_{suffix}"

        # File extension
        filename = f"{filename}.fits"

        return filename
    
    def generate_filename(
        self,
        suffix: str | None = None,
        #origin : str | None = None,
        #auto_version : bool = None,
    ):

        # Version
        # skip_version = get_env_var_bool('KOA_SKIP_CALIBRATION_VERSION', default=False)
        # cache_defined = isinstance(os.getenv('KOA_CALIBRATION_CACHE'), str)
        # if not skip_version and cache_defined and auto_version is not False:
        #     if self.meta.cal_version is None and auto_version:
        #         self.generate_calibration_version(origin=origin)

        # Make filename
        filename = self._generate_filename(
            instrument_name=self.meta.instrument.name,
            datetime_obs=self.meta.datetime_obs,
            detector=self.meta.instrument.detector,
            cal_type=self._cal_type,
            master_cal=self.meta.master_cal,
            cal_version=self.meta.cal_version,
            origin=self.meta.origin,
            suffix=suffix
        )

        # Set new filename
        self.meta.filename = filename

        # Set new filepath if input dir already exists.
        # NOTE: This behavior might change in the future.
        if self._filepath is not None:
            input_dir = os.path.dirname(os.path.abspath(self._filepath))
            self._filepath = os.path.join(input_dir, self.meta.filename)

        # Update KOA ID and filepath
        _set_koa_meta(self)

        return self.meta.filename
    
    def generate_calibration_id(self) -> str:
        """
        Generate UUID.

        Returns
        -------
        cal_id : str
            The calibration file ID
        """
        self.meta.cal_id = str(make_uuid4())
        return self.meta.cal_id
    
    # def generate_calibration_version(self, origin : str | None = None) -> str:
    #     """
    #     Generate a unique version string for the calibration file
    #     and set it at ``self.meta.cal_version``.

    #     Parameters
    #     ----------
    #     origin : str | None
    #         The origin of the calibration file.

    #     Returns
    #     -------
    #     cal_version : str
    #         The calibration version string.
    #     """
    #     from ..calibrations import LigerCalibrationStore
    #     if origin is not None:
    #         self.meta.origin = origin
    #     if self.meta.origin is None:
    #         self.meta.origin = os.getenv('KOA_CALIBRATION_ORIGIN', 'LOCAL')
    #     with LigerCalibrationStore(
    #         connect_remote=False
    #     ) as store:
    #         self.meta.cal_version = store.generate_calibration_version(
    #             self, origin=self.meta.origin
    #         )
    #     return self.meta.cal_version