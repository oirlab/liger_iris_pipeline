from __future__ import annotations
import gc
import logging

import yaml
from typing import Sequence
import astropy.time
import numpy as np
from astropy.utils.decorators import classproperty
import os

import liger_iris_pipeline
from .. import datamodels
from ..datamodels import LigerIRISDataModel, CalibrationModel
from ..utils.config import get_config_path

import stpipe
import stpipe.utilities
from stpipe import Step
from stpipe import config_parser
from .._version import __version__

from jwst.stpipe._cal_logs import _LOG_FORMATTER

from koa_middleware import CalibrationSelector
from koa_middleware.utils import is_valid_uuid

__all__ = ["LigerIRISStep"]

logger = logging.getLogger(__name__)

class LigerIRISStep(Step):
    """
    Base class for all LigerIRIS Steps.
    """

    # NOTE: Using the same log formatter as jwst for now. Consider customizing later.
    _log_records_formatter = _LOG_FORMATTER

    calibrations = {}

    spec = """
        output_ext = string(default='.fits')  # Output file extension
        output_model = pass(default=None) # Output datamodel, see Step._get_output_model
        max_cores = integer(default = 1) # Maximum number of CPU cores to use.
    """

    def __init__(self, *args, **kwargs):
        self._calibrations_used = {}
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_stpipe_loggers():
        """
        Get the names of loggers to configure.
        See https://github.com/spacetelescope/jwst/blob/main/jwst/stpipe/core.py#L84 for jwst implementation, which we modify below.
        Implemented for compatibility with stpipe.

        Returns
        -------
        loggers : tuple of str
            Tuple of log names to configure.
        """
        # Specify the log names for any dependencies whose
        # loggers we want to configure and for the special "py.warnings"
        # logger which is the source of warning log messages for python warnings
        return ("liger_iris_pipeline", "stcal", "stdatamodels", "stpipe", "tweakwcs", "py.warnings", "koa_middleware")

    @classmethod
    def _datamodels_open(cls, init, **kwargs):
        """
        Open a datamodel using the datamodels.open method in the context of this class.
        Implemented for compatibility with stpipe.
        Users should call `Step.open_model`.
        """
        return datamodels.open(init, **kwargs)
    
    def open_model(self, init, **kwargs):
        """
        Open a datamodel using the datamodels.open method in the context of this class.
        Implemented for compatibility with stpipe. Wrapper for Step._datamodels_open.

        Parameters
        ----------
        init : object
            The object to open.
        """
        return self._datamodels_open(init, **kwargs)

    def finalize_result(self, result, calibration_files_used : dict | None = None):
        """
        Update the result with the software version and references used.
        Implemented for compatibility with stpipe.

        Parameters
        ----------
        result
            The result to finalize.
        """
        if self._status is None:
            self._status = "COMPLETED"
        self._datetime_end = astropy.time.Time.now().isot
        if isinstance(result, datamodels.LigerIRISDataModel):
            self.finalize_model(result, calibration_files_used)
        elif isinstance(result, Sequence):
            for model in result:
                if isinstance(model, datamodels.LigerIRISDataModel):
                    self.finalize_model(model, calibration_files_used)
        elif isinstance(result, dict):
            for key, model in result.items():
                if isinstance(model, datamodels.LigerIRISDataModel):
                    self.finalize_model(model, calibration_files_used)
        return result
    
    def finalize_model(self, model : datamodels.LigerIRISDataModel, calibration_files_used : dict | None = None):
        """
        Finalize the given model by adding receipt entry and setting software version.

        Parameters
        ----------
        model : LigerIRISDataModel
            The model to finalize.
        """

        # Step status
        try:
            setattr(model.meta.step, self.class_alias, self._status)
        except Exception as e:
            logger.warning(f"Could not set step status for {model.meta.step}.{self.class_alias}: {e}")

        # Full receipt entry of step
        self.add_receipt_entry(model, self._calibrations_used)

        # Reference file information
        if calibration_files_used is not None and len(calibration_files_used) > 0:
            for role, cal_info in calibration_files_used.items():
                try:
                    getattr(model.meta.cal_file, cal_info['cal_type']).filename = cal_info['filename']
                    getattr(model.meta.cal_file, cal_info['cal_type']).id = cal_info['id']
                except Exception as e:
                    logger.warning(f"Could not set calibration file information for {model.meta.cal_file}.{cal_info['cal_type']}: {e}")
        
                self.add_calibration_entry(
                    model,
                    cal_info,
                    role=role,
                )

        # Other metadata updates
        model.meta.drp_version = __version__

        return model

    def save_model(
        self, model,
        output_path : str | None = None,
        output_dir : str | None = None,
        output_filename : str | None = None,
        suffix : str | None = None
    ):
        """
        Saves the given model using the step/pipeline's naming scheme.

        Args:
            See `Step.make_output_path` for argument information.

        Returns:
            (str): The full path to the saved model.
        """
        if output_path:
            output_path = model.save(output_path)
        else:
            if output_dir is None:
                output_dir = self.output_dir
            if output_filename is None:
                output_filename = model._filepath
            filepath = self.make_output_path(model, filename=output_filename, output_dir=output_dir, suffix=suffix)
            filepath = model.save(output_path)

        # Log
        logger.info(f"Saved model in {output_path}")

        # Return the filepath
        return filepath
    
    def run(self, *args, **kwargs):
        """
        Run handles the generic setup and teardown that happens with
        the running of each step.  The real work that is unique to
        each step type is done in the ``process`` method.

        Parameters
        ----------
        args : See particular Step.process method for valid inputs.

        Notes
        -----
        This overrides stpipe.Step.run to provide additional functionality
        and compatibility with Liger/IRIS data.
        """

        self._status = None
        self._calibrations_used = {}
        self._datetime_start = astropy.time.Time.now().isot

        with stpipe.log.record_logs(
            log_names=self.get_stpipe_loggers(), formatter=self._log_records_formatter
        ) as log_records:
            
            self._log_records = log_records
            
            # Set new parameters
            step_result = None
            for key, value in kwargs.items():
                if key not in ('step_defs',):
                    setattr(self, key, value)

            # GC
            gc.collect()

            logger.info("Step %s running with args %s.", self.name, args)
            # log Step or Pipeline parameters from top level only
            if self.parent is None:
                logger.info(
                    "Step %s parameters are:%s",
                    self.name,
                    # Add an indent to each line of the YAML output
                    "\n  "
                    + "\n  ".join(
                        yaml.dump(self.get_pars(), sort_keys=False)
                        .strip()
                        # Convert serialized YAML types true/false/null to Python types
                        .replace(" false", " False")
                        .replace(" true", " True")
                        .replace(" null", " None")
                        .splitlines()
                    ),
                )

            if len(args):
                self.set_primary_input(args[0])

            # Default output file configuration
            if self.output_file is not None:
                self.save_results = True

            if self.suffix is None:
                self.suffix = self.default_suffix()

            hook_args = args
            for pre_hook in self._pre_hooks:
                hook_results = pre_hook.run(*hook_args)
                if hook_results is not None:
                    hook_args = (hook_results,)
            args = hook_args

            # Warn if passing in objects that should be
            # discouraged.
            #self._check_args(args, stpipe.step.DISCOURAGED_TYPES, "Passed")

            # NOTE: This diverges from stpipe behavior.
            # NOTE: Below is uncommented in stpipe.
            # if self.parent is None:
            #     if self.skip:
            #         logger.info("Step run as standalone, so skip set to False")
            #         self.skip = False

            # If step is skipped
            # NOTE: This is NOT redundant with below
            if self.skip:
                logger.info("Step skipped.")
                self._status = "SKIPPED"
                step_result = args[0]
            
            # Get calibrations if not skipped
            # NOTE: Skip prefetch, not implemented for Liger/IRIS yet!
            #if not self.skip and self.prefetch_references:
            #    self.prefetch(*args)

            # Run the main process of the step
            if not self.skip:
                try:
                    step_result = self.process(*args)
                except TypeError as e:
                    if "process() takes exactly" in str(e):
                        raise TypeError("Incorrect number of arguments to step") from e
                    raise

            # Step.process() can also determine to skip a step dynamically, so check again
            # NOTE: This is NOT redundant with above
            if self.skip or self._status == "SKIPPED":
                self.skip = True
                self._status = "SKIPPED"
                logger.info("Step skipped.")
                step_result = args[0]

            # Run the post hooks
            for post_hook in self._post_hooks:
                hook_results = post_hook.run(step_result)
                if hook_results is not None:
                    step_result = hook_results

            # Update meta information
            if not isinstance(step_result, Sequence):
                results = [step_result]
            else:
                results = step_result

            # The finalize_result hook allows subclasses to add
            # metadata (like the cal code package version) before
            # the result is saved.
            for result in results:
                self.finalize_result(result, self._calibrations_used)

            # Save the output file if one was specified
            if not self.skip and self.save_results:
                # Setup the save list.
                if not isinstance(step_result, list | tuple):
                    results_to_save = [step_result]
                else:
                    results_to_save = step_result

                for idx, result in enumerate(results_to_save):
                    if len(results_to_save) <= 1:
                        idx = None
                    if isinstance(result, stpipe.datamodel.AbstractDataModel):
                        self.save_model(result, idx=idx)
                    elif hasattr(result, "save"):
                        try:
                            output_path = self.make_output_path(idx=idx)
                        except AttributeError:
                            logger.warning(
                                "`save_results` has been requested, but cannot"
                                " determine filename."
                            )
                            logger.warning(
                                "Specify an output file with `--output_file` or set"
                                " `--save_results=false`"
                            )
                        else:
                            logger.info("Saving file %s", output_path)
                            result.save(output_path, overwrite=True)

            if not self.skip:
                logger.info("Step %s done", self.name)

            if not self.parent:
                logger.info(f"Results used liger_iris_pipeline version: {__version__}")

        return step_result
    
    def get_reference_file(self, *args, **kwargs):
        return self.get_calibration(*args, **kwargs)

    def get_calibration(
        self,
        input : str | LigerIRISDataModel,
        role : str,
        selector : CalibrationSelector | None = None,
        use_cached : bool | None = None,
    ) -> tuple[str | LigerIRISDataModel, dict | None]:
        """
        Primary method for a primitive to call in order to get a reference file in the context of a primitive.

        Parameters
        ----------
        input : str or LigerIRISDataModel
            The filepath or datamodel to get a reference file for.
        role : str
            The role of reference file in this primitive, which should match a key in
            ``self.calibrations``.
        selector : CalibrationSelector or None
            An optional selector to use instead of the default selector
            defined in ``self.calibrations``.
        use_cached : bool or None
            If True, use cached reference files if available. If None, use the
            default setting from the configuration.

        Returns
        -------
        tuple[str | DataModel, dict | None]:
            A tuple of (reference_file_or_model, reference_record).
        """

        # User provided value
        cal_value = getattr(self, role, None)

        # Input model
        input_model = datamodels.open(input, meta_only=True)

        from ..calibrations import LigerCalibrationStore

        ####################
        #### Case 1: ID ####
        ####################
        if isinstance(cal_value, str) and is_valid_uuid(cal_value):
            cal_id = cal_value
            with LigerCalibrationStore(
                use_cached=use_cached
            ) as store:
                
                local_filepath, cal_record = store.get_calibration(calibration=cal_id)
                
                self._calibrations_used[role] = cal_record

                logger.info(
                    f"Calibration role={role}: Using file={cal_record['filename']} ID={cal_record['id']} for input={input_model}"
                )
                
                return local_filepath, cal_record

        ###############################################################
        #### Case 2: filepath string or datamodel (uuid ruled out) ####
        ###############################################################
        if isinstance(cal_value, (str, LigerIRISDataModel)):

            # Open to get cal id (open in full mode to return for processing)
            if isinstance(cal_value, str):

                if os.path.isfile(cal_value):
                    cal_model = datamodels.open(cal_value)
                elif os.path.isfile(os.path.join(os.environ['KOA_CALIBRATION_CACHE'], cal_value)):
                    cal_filepath = os.path.join(os.environ['KOA_CALIBRATION_CACHE'], cal_value)
                    cal_model = datamodels.open(cal_filepath)

            elif isinstance(cal_value, datamodels.CalibrationModel):
                cal_model = cal_value

            assert isinstance(
                cal_model, datamodels.CalibrationModel
            ), "Input must be a valid CalibrationModel."

            cal_record = cal_model.to_record()
            self._calibrations_used[role] = cal_record

            logger.info(
                f"Calibration role={role}: Using file={cal_record['filename']} ID={cal_record['id']} for input={input_model}"
            )

            return cal_model, cal_record

        ######################################
        #### Case 3: Selector config dict ####
        ######################################
        if isinstance(cal_value, dict) and 'selector' in cal_value and 'selector_kwargs' in cal_value:

            selector_class = cal_value.get(
                'selector',
                self.calibrations[role]['selector']
            )
            selector_kwargs = cal_value.get(
                'selector_kwargs',
                self.calibrations[role]['selector_kwargs']
            )
            selector = selector_class(**selector_kwargs)
            
            with LigerCalibrationStore(
                use_cached=use_cached
            ) as store:
                local_filepath, cal_record = store.select_and_get_calibration(
                    input_model.meta,
                    selector=selector
                )
            
            self._calibrations_used[role] = cal_record
            logger.info(
                f"Calibration role={role}: Using file={cal_record['filename']} ID={cal_record['id']} for input={input_model}"
            )

            return local_filepath, cal_record

        ######################################
        #### Case 4: Calibration Selector ####
        ######################################
        if isinstance(cal_value, CalibrationSelector):

            selector = cal_value
            input_model = datamodels.open(input, meta_only=True)

            with LigerCalibrationStore(
                use_cached=use_cached
            ) as store:
                
                local_filepath, cal_record = store.select_and_get_calibration(
                    input_model.meta,
                    selector=selector
                )
            
            self._calibrations_used[role] = cal_record

            logger.info(
                f"Calibration role={role}: Using file={cal_record['filename']} ID={cal_record['id']} for input={input_model}"
            )

            return local_filepath, cal_record

        ########################################################################
        ##### Case 5: None - use default selector from calibrations ####
        ########################################################################
        if cal_value is None:
            if selector is None:
                if not hasattr(self, 'calibrations') or role not in self.calibrations:
                    raise ValueError(f"No reference file configuration found for '{role}' in calibrations")

                ref_config = self.calibrations[role]
                selector_class = ref_config['selector']
                selector_kwargs = ref_config.get('selector_kwargs', {})
                selector = selector_class(**selector_kwargs)
            
            with LigerCalibrationStore(
                use_cached=use_cached
            ) as store:
                
                local_filepath, cal_record = store.select_and_get_calibration(
                    input_model.meta,
                    selector=selector
                )

            self._calibrations_used[role] = cal_record

            logger.info(
                f"Calibration role={role}: Using file={cal_record['filename']} ID={cal_record['id']} for input={input_model}"
            )
            return local_filepath, cal_record

        # Else raise error
        msg = f"Invalid calibration value for '{role}': {type(cal_value)}"
        logger.error(msg)
        raise ValueError(msg)

    def make_output_path(
        self,
        model : LigerIRISDataModel,
        output_dir : str | None = None,
        filename : str | None = None,
        suffix : str | None = None
    ) -> str:
        """
        Generate the output path for the given model in the context of this Step instance.

        Parameters
        ----------
        model : LigerIRISDataModel
            The model to generate the output path for.
        output_dir : str, optional
            The directory to save the output file. Defaults to ``self.output_dir``.
        filename : str, optional
            The filename to save the output file. Defaults to model.meta.filename
        suffix : str, optional
            An optional suffix to add to the filename. Defaults to ``self.suffix``.

        Returns
        -------
        str
            The full path to save the output file.
        """
        if output_dir is None:
            output_dir = self.output_dir
        if suffix is None:
            suffix = self.suffix
        return self._make_output_path(model, output_dir=output_dir, filename=filename, suffix=suffix)

    @staticmethod
    def _make_output_path(
        model : LigerIRISDataModel,
        output_dir : str | None,
        filename : str | None,
        suffix : str | None
    ) -> str:
        """
        Generate the output path for the given model with no Step instance.

        Args:
            model (LigerIRISDataModel): The model to generate the output path for.
            output_dir (str, optional): The directory to save the output file. Defaults to `os.path.basename(model._filename)`.
            filename (str, optional): The filename to save the output file. Defaults to model.meta.filename
            suffix (str, optional): An optional suffix to add to the filename.

        Returns:
            str: The full path to save the output file.
        """
            
        # Determine the directory
        if output_dir is None:
            if model._filename is not None:
                output_dir = os.path.dirname(os.path.abspath(model._filepath))
            else:
                output_dir = os.getcwd()
        
        # Determine the filename
        if filename is None:
            if model.meta.filename is not None:
                filename = model.meta.filename
            else:
                filename = model.generate_filename()
        else:
            filename = model.generate_filename()
        if suffix is None:
            suffix = ''
        else:
            suffix = '_' + suffix

        # Add suffix to filename
        filename = os.path.splitext(filename)[0] + suffix + os.path.splitext(filename)[1]

        # Final path
        output_path = os.path.join(output_dir, filename)

        # Return the path
        return output_path

    @classmethod
    def load_spec_file(cls, preserve_comments=stpipe.utilities._not_set):
        """
        Extension of Step.load_spec_file.
        Load the merged parameters for this class from the spec attributes.
        Implemented for compatibility with stpipe.

        Notes
        -----
        stpipe.Step.load_spec_file needs access to crds_client to get override names
        for references, so we override load_spec_file here to skip those lines.

        Parameters
        ----------
        preserve_comments : bool
            Whether to preserve comments in the spec file.
        """
        spec = config_parser.get_merged_spec_file(
            cls, preserve_comments=preserve_comments
        )
        # Add arguments for all of the expected reference files to spec
        for cal_role in cls.calibrations:
            #override_name = crds_client.get_override_name(reference_file_type)
            spec[cal_role] = "is_string_or_datamodel(default=None)"
            spec.inline_comments[cal_role] = (
                f"# Override the {cal_role} calibration"
            )
        return spec
    
    # @classmethod
    # def build_config(cls, input, **kwargs):
    #     # TODO: Implement!
    #     raise NotImplementedError("LigerIRISStep.build_config is not implemented yet.")

    @classmethod
    def get_config_from_reference(cls, dataset, disable=None, crds_observatory=None):
        """
        Retrieve step parameters from the reference database.

        Parameters
        ----------
        cls : stpipe.Step
            Either a class or instance of a class derived
            from ``Step``.
        dataset : AbstractDataModel or dict
            A model of the input file.  Metadata on this input file will
            be used by the CRDS "bestref" algorithm to obtain a reference
            file. If a dict, crds_observatory must be a non-None value.
        disable: bool or None
            Do not retrieve parameters from CRDS. If None, check global settings.
        crds_observatory : str
            Observatory name ('tmt' or 'keck').

        Returns
        -------
        step_parameters : configobj
            The parameters as retrieved from CRDS. If there is an issue, log as such
            and return an empty config obj.
        """
        reftype = cls.get_config_reftype()
        logger.debug("No %s reference files found.", reftype.upper())
        return config_parser.ConfigObj()
    
    def add_receipt_entry(self, model : datamodels.LigerIRISDataModel, calibration_files_used : dict | None = None):
        """
        Add an entry to the receipt table of the model summarizing the processing.

        Parameters
        ----------
        model : DataModel
            The data model to add the receipt entry to.
        """
        pars = self.get_pars()
        del pars['pre_hooks'], pars['post_hooks']
        del pars['skip']
        del pars['output_file']
        del pars['save_results']
        del pars['search_output_file']
        del pars['output_dir']
        del pars['suffix']
        del pars['output_use_model']
        del pars['output_use_index']
        del pars['output_ext']
        del pars['input_dir']
        pars_str = "" if len(pars) == 0 else (
            yaml.dump(
                pars,
                sort_keys=False,
                default_flow_style=True,
            )
            .strip()
            .replace(" false", " False")
            .replace(" true", " True")
            .replace(" null", " None")
        )

        if calibration_files_used is None or len(calibration_files_used) == 0:
            cal_files_str = ""
        else:
            cal_files_str = repr(calibration_files_used)

        row = {
            'CLASS': f"{self.__class__.__module__}.{self.__class__.__name__}".encode(),
            'PROC_START_TIME': self._datetime_start.encode(),
            'PROC_END_TIME': self._datetime_end.encode(),
            'FILENAME': model.meta.filename or 'None'.encode(),
            'PARAMETERS': pars_str.encode(),
            'CALIBRATIONS': cal_files_str.encode(),
            'DRP_VERSION': liger_iris_pipeline._version.__version__.encode(),
            'DRP_GIT_COMMIT_ID': liger_iris_pipeline._version.__commit_id__.encode(),
            'STATUS': self._status.encode(),
        }

        row_tuple = tuple(row.values())
        row_arr = np.array([row_tuple], dtype=model.receipt.dtype)
        model.receipt = np.append(model.receipt, row_arr)

        return model
    
    def add_calibration_entry(
        self,
        model : LigerIRISDataModel,
        cal : CalibrationModel | str | dict,
        role : str,
    ):
        """
        Add a calibration to the DataModel's calibration files table.

        Parameters
        ----------
        model : LigerIRISDataModel
            The data model to add the reference file to.
        cal : CalibrationModel | str | dict
            The reference file to add. Can be:

                - DataModel object
                - String filepath (will load metadata to create entry)
                - Dict with reference file column values

        role : str
            The role of the reference file.
        """

        # Case 1: Either metadata dict or SQL record (dict)
        # Assume same keys for now
        # NOTE: Ignore this case for now, always pass entire datamodel.
        # if isinstance(cal, stdatamodels.properties.ObjectNode):
        #     new_row = {
        #         'CAL_ROLE': role,
        #         'FILENAME' : cal['filename'] or 'None',
        #         'TIME_APPLIED' : self._datetime_start,
        #         'CAL_TYPE' : cal['cal_type'],
        #         'DATETIME_OBS' : cal['datetime_obs'],
        #         'LAST_PROCESSED' : cal['last_processed'],
        #         'ID' : cal['cal_id'],
        #         'CLASS' : self.__class__.__name__,
        #         'DRP_VERSION' : cal['drp_version'],
        #     }

        # Calibration DB record
        if isinstance(cal, dict):
            new_row = {
                'ROLE': role,
                'CAL_TYPE' : cal['cal_type'],
                'FILENAME' : cal['filename'] or 'None',
                'ID' : cal['id'],
                'DATETIME_OBS' : cal['datetime_obs'],
                'LAST_PROCESSED' : cal['last_processed'],
                'TIME_APPLIED' : self._datetime_start,
                'CLASS' : self.__class__.__name__,
                'DRP_VERSION' : cal['drp_version'],
            }

        # Case 2: filepath or DataModel
        # NOTE: This path should be used with caution
        #   and limited to dev purposes or limited user cases, never at Keck.
        elif isinstance(cal, (str, CalibrationModel)):
            from ..datamodels import open as open_datamodel
            cal_model = open_datamodel(cal, meta_only=True)
            new_row = {
                'ROLE': role,
                'CAL_TYPE' : cal_model.meta.cal_type,
                'FILENAME' : cal_model.meta.filename or 'None',
                'ID' : cal_model.meta.cal_id,
                'DATETIME_OBS' : cal_model.meta.datetime_obs or 'None',
                'LAST_PROCESSED' : cal_model.meta.last_processed or None,
                'TIME_APPLIED' : self._datetime_start,
                'CLASS' : self.__class__.__name__,
                'DRP_VERSION' : cal_model.meta.drp_version,
            }
        else:
            raise ValueError("Invalid reference file input")

        row_tuple = tuple(new_row.values())
        row_arr = np.array([row_tuple], dtype=model.calibrations.dtype)
        model.calibrations = np.append(model.calibrations, row_arr)

    @classproperty
    def reference_file_types(cls):
        """
        Implemented for compatibility with stpipe.Step,
        since we override "reference_files" with "calibrations".
        """
        if hasattr(cls, 'calibrations'):
            return list(cls.calibrations.keys())
        return []
    
    def default_suffix(self):
        """
        Return a default suffix based on the step.

        This overrides the default method Step.default_suffix() which returns self.name.lower().
        
        Instead, this method returns proc-{self.class_alias.lower()}.
        """
        return f'proc-{self.class_alias.lower()}'
    
    @classmethod
    def from_config_file(cls, config_file, parent=None, name=None):
        """
        Initialize a Step or Pipeline from a configuration file.

        Parameters
        ----------
        config_file : str
            The path to the configuration file.
            Optionally, a config file in liger_iris_pipeline/configs/ can be specified.

        Returns
        -------
        LigerIRISStep
             An instance of the Step or Pipeline with the configuration loaded.
        """

        # Resolve config file path
        config_filepath = get_config_path(config_file)
        
        # Load config file
        # NOTE: This destroys nested config_files
        config = config_parser.load_config_file(config_filepath)

        # Resolve class name
        class_name = config.get('class', None)
        if class_name is None:
            raise ValueError("Config file must specify a 'class' key with the full class name of the class to initialize.")
        
        # If a file object was passed in, pass the file name along
        #if hasattr(config_file, "name"):
        #    config_file = config_file.name
        
        step_class, name = cls._parse_class_and_name(config)

        # If only a step, intiialize with default behavior
        # Since we have to load the config file first to determine the class,
        # we don't invoke super().from_config_file.
        from .base_pipeline import LigerIRISPipeline
        if not issubclass(step_class, LigerIRISPipeline):
            return step_class.from_config_section(
                config,
                parent=parent,
                name=name,
                config_file=config_file,
            )

        # Construct pipeline class
        pipe = step_class.from_config_section(
            config,
            parent=parent,
            name=name,
            config_file=config_file,
        )

        breakpoint()

        return pipe

        #return pipe

        # return step_class.from_config_section(
        #     config,
        #     parent=parent,
        #     name=name,
        #     config_file=config_file,
        # )

        #step = super().from_config_file(config_filepath)

        # # Default arguments
        # if 'arguments' not in self.config:
        #     self.config['arguments'] = self.ARGUMENTS.copy()
        # else:
        #     self.config['arguments'] = self.ARGUMENTS | self.config['arguments']

        # # Default logging
        # if 'logging' not in self.config:
        #     self.config['logging'] = self.LOGGING.copy()
        # else:
        #     self.config['logging'] = self.LOGGING | self.config['logging']

        # # Ensure primitives dict exists
        # if 'primitives' not in self.config:
        #     self.config['primitives'] = {}

        # def _deep_merge(d1: dict, d2: dict) -> dict:
        #     result = d1.copy()
        #     for k, v in d2.items():
        #         if (
        #             k in result
        #             and isinstance(result[k], dict)
        #             and isinstance(v, dict)
        #         ):
        #             result[k] = _deep_merge(result[k], v)
        #         else:
        #             result[k] = v
        #     return result

        # # Populate primitive configs
        # for prim_alias in self.PRIMITIVES:

        #     # Set default primitive config dict
        #     if prim_alias in self.config['primitives']:
        #         prim_config = self.config['primitives'][prim_alias]
        #     else:
        #         self.config['primitives'][prim_alias] = {}
        #         prim_config = self.config['primitives'][prim_alias]

        #     # Primitive config file
        #     if 'config_file' in prim_config:
        #         prim_config_file = get_config_path(prim_config['config_file'])
        #         prim_config_from_file = read_config_file(prim_config_file)
        #         del prim_config['config_file']
        #     else:
        #         prim_config_from_file = {}

        #     # Merge file config with inline config
        #     prim_config = _deep_merge(prim_config_from_file, prim_config)

        #     # Set primitive class name
        #     prim_class_name = self.PRIMITIVES[prim_alias].__module__ + '.' + self.PRIMITIVES[prim_alias].__name__
        #     prim_config['class'] = prim_class_name

        #     # Ensure arguments dict exists
        #     if 'arguments' not in prim_config:
        #         prim_config['arguments'] = {}

        #     # Pass pipeline logging to primitive (primitive overrides allowed)
        #     prim_config['logging'] = self.config['logging'] | prim_config.get('logging', {})

        #     # Set primitive config
        #     self.config['primitives'][prim_alias] = prim_config

        # return self.config