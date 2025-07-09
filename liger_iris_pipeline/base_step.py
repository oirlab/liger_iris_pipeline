
from functools import wraps
from collections.abc import Sequence
import warnings
import gc

import stpipe.utilities
from . import datamodels
from .datamodels import LigerIRISDataModel
import stpipe.log
import os


import stpipe
from stpipe import Step
from stpipe import config_parser
from . import datamodels
from . import __version__

from stpipe import crds_client

__all__ = ["LigerIRISStep"]

class LigerIRISStep(Step):
    """
    Here we override several core methods from stpipe.step.Step to provide:
    1. Manual control on deriving the configuration from spec, a config file, and additional kwargs.
    2. Broader signatures for run, process, (and eventually call if appropriate).
    Once the DRS is robust enough, we will realign (although not completely) with stpipe.step.Step methods.
    """

    exclude_spec = [
        "pre_hooks", "post_hooks",
        "output_use_index", "output_use_model",
        "search_output_file", "input_dir", 'output_ext',
        'steps' # Make spec only contain config for THIS class, not substeps
    ]

    def __init__(
            self,
            config_file : str | None = None,
            **kwargs
        ):
        """
        Create a `Step` instance.
        Configuration is determined according to:
            1. Class's spec object
            2. config_file
            3. kwargs
        """
        self.init_logger()
        self._reference_files_used = []

        # TODO: Refactor this back into stpipe Step classmethods where appropriate.

        # Load config for this Step (not a pipeline)
        self.config_file = config_file

        if self.config_file is not None:
            config = config_parser.load_config_file(config_file)
        else:
            config = config_parser.ConfigObj()
        
        # Parse the config from the spec and any provided kwargs
        spec = self.load_spec_file()
        kwargs = config_parser.config_from_dict(
            kwargs,
            spec,
            root_dir=None,
            allow_missing=False
        )

        # Merge the spec with the config
        config.merge(kwargs)

        # Set the config parameters as member variables
        for key, val in config.items():
            if key not in ("class", "steps", "config_file"):
                _val = self.parse_config_kwarg(key, val, spec)
                setattr(self, key, _val)


    def process(self, input : str | LigerIRISDataModel):
        """
        This is where real work happens. Every Step subclass has to
        override this method. The default behaviour is to raise a
        NotImplementedError exception. The signature must be `process(self, input : str | LigerIRISDataModel)`.
        """
        raise NotImplementedError(f"Class {self.__class__} does not implement instance method `process`.")
    

    @classmethod
    def _datamodels_open(cls, init, **kwargs):
        """
        Open a datamodel using the datamodels.open method. Implemented for compatibility with stpipe.
        """
        return datamodels.open(init, **kwargs)
    
    
    def open_model(self, name : str | LigerIRISDataModel, copy : bool = False):
        """
        Open a model from a file or copy an existing datamodel in the context of this Step.
        Any Step that opens a DataModel should call this method.

        Args:
            name (str | LigerIRISDataModel): The name of the file or the datamodel to open.
            copy (bool, optional): Copy and return the input if already a `LigerIRISDataModel`. Defaults to False.

        Returns:
            (LigerIRISDataModel): The opened or copied datamodel.
        """
        if isinstance(name, LigerIRISDataModel):
            if copy:
                return name.copy()
            else:
                return name
        if isinstance(name, str):
            return datamodels.open(name)
        else:
            raise ValueError(f"Cannot open model from {name}")
    

    def finalize_result(self, result : LigerIRISDataModel, reference_files_used : dict[str, str] | None = None):
        """
        Finalize the result by updating metadata.

        Args:
            result (LigerIRISDataModel): The result to finalize.
            reference_files_used (dict[str, str]): The reference files used in the processing.

        Returns:
            (LigerIRISDataModel): The finalized result. Updates are in-place.
        """
        result.meta.drs_version = __version__
        from .pipeline import LigerIRISPipeline
        if not isinstance(self, LigerIRISPipeline):
            if hasattr(result.meta.drs_step, f"{self.class_alias}"):
                setattr(result.meta.drs_step, f"{self.class_alias}", self.status)
            else:
                self.log.warning(f"Could not update status for {result.meta.drs_step}.{self.class_alias} in datamodel.")

        # Set references files used
        if reference_files_used is not None and len(reference_files_used) > 0:
            for ref_name, filename in reference_files_used:
                if hasattr(result.meta.ref_file, ref_name):
                    getattr(result.meta.ref_file, ref_name).name = filename
            
            # Set CRDS context and software version
            result.meta.ref_file.crds.sw_version = crds_client.get_svn_version()
            result.meta.ref_file.crds.context_used = crds_client.get_context_used(result.crds_observatory)

            if self.parent is None:
                self.log.info(f"Results used CRDS context: {result.meta.ref_file.crds.context_used}")

        # Reset status
        self.status = None

        # Return the result
        return result


    @wraps(Step.__call__)
    def __call__(self, *args, **kwargs):
        if not self.parent:
            warnings.warn(
                "Step.__call__ is deprecated. It is equivalent to Step.run "
                "and is not recommended.",
                UserWarning
            )
        return super().__call__(*args, **kwargs)


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
        self.log.info(f"Saved model in {output_path}")

        # Return the filepath
        return filepath


    def run(self, input, **kwargs):
        """
        Run handles the generic setup and teardown that happens with the running of each step. The real work that is unique to each step type is done in the `process` method.

        Args:
            input (str | LigerIRISDataModel): The input to process:
                1. filename of datamodel
                2. filename of ASN
                3. datamodel
                4. ASN
            
            ``**kwargs``: Additional spec parameters to pass to the step.

        Returns:
            (LigerIRISDataModel | list[LigerIRISDataModel]): The result(s) of the step. Steps can only return a single model, but Pipelines can return a list of datamodels.
        """
        gc.collect()
        
        with stpipe.log.record_logs(formatter=self._log_records_formatter) as log_records:

            self._log_records = log_records

            # Make generic log messages go to this step's logger
            orig_log = stpipe.log.delegator.log
            stpipe.log.delegator.log = self.log

            step_result = None

            # Update the params based on kwargs
            self.update_pars(kwargs)
            pars = self.get_pars()
            pars = '\n'.join(f"{k}={repr(v)}" for k, v in pars.items())

            # log Step or Pipeline parameters from top level only
            if self.parent is None:
                self.log.info(
                    f"Running step {self} with parameters:\n{pars}"
                )
            
            # Main try block
            try:

                # Prefetch references
                self._reference_files_used = []
                if not self.skip and self.prefetch_references:
                    self.prefetch(input)

                # Call process and catch signature error
                if not self.skip:
                    try:
                        step_result = self.process(input)
                    except TypeError as e:
                        if "process() takes exactly" in str(e):
                            raise TypeError(
                                "Incorrect number of arguments to step"
                            ) from e
                        raise
                else:
                    step_result = self.on_skip(input)
                    self.log.info(f"Skipping step {self.name}")

                # Update meta information regardless of skip
                if isinstance(step_result, Sequence):
                    for result in step_result:
                        self.finalize_result(result, self._reference_files_used)
                else:
                    self.finalize_result(step_result, self._reference_files_used)

                self._reference_files_used = [] # Reset?

                # Save the results even if skipped since metadata is udpated.
                if self.save_results:
                    if isinstance(step_result, Sequence):
                        for result in step_result:
                            self.save_model(result, output_dir=self.output_dir)
                    else:
                        self.save_model(step_result, output_dir=self.output_dir)

                if not self.skip:
                    self.log.info(f"Step {self.name} done")
            finally:
                stpipe.log.delegator.log = orig_log
        return step_result


    def init_logger(self, config : config_parser.ConfigObj | None = None):
        """
        Initialize logging for the step.
        Config ignored for now.
        """
        # A list of logging.LogRecord emitted to the stpipe root logger
        # during the most recent call to Step.run.
        self._log_records = []

        # Namespace for the logger
        self.name = self.__class__.__name__
        self.qualified_name = f"{stpipe.log.STPIPE_ROOT_LOGGER}.{self.name}"
        self.parent = None
        self.log = stpipe.log.getLogger(self.qualified_name)
        self.log.setLevel(stpipe.log.logging.DEBUG)
        self.log.info(f"{self.__class__.__name__} instance created.")


    def make_output_path(
        self,
        model : LigerIRISDataModel,
        output_dir : str | None = None,
        filename : str | None = None,
        suffix : str | None = None
    ) -> str:
        """
        Generate the output path for the given model in the context of this Step instance.

        Args:
            model (LigerIRISDataModel): The model to generate the output path for.
            output_dir (str, optional): The directory to save the output file. Defaults to `self.output_dir`.
            filename (str, optional): The filename to save the output file. Defaults to model.meta.filename
            suffix (str, optional): An optional suffix to add to the filename. Defaults to `self.suffix`.

        Returns:
            (str): The full path to save the output file.
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
        Load the merged parameters for this class from the spec attributes.
        """
        spec = super().load_spec_file(preserve_comments=preserve_comments)
        for k in cls.exclude_spec:
            if k in spec:
                del spec[k]
        return spec
    

    def get_pars(self, full_spec : bool = True):
        """
        Get the current parameters for this step.

        Args:
            full_spec (bool, optional): If True, return the full spec. Defaults to True.
        """
        pars_dict = super().get_pars(full_spec=full_spec)
        for k in self.exclude_spec:
            if k in pars_dict:
                del pars_dict[k]
        return pars_dict
    

    @staticmethod
    def parse_config_kwarg(key : str, val : str | None, spec):
        """
        TODO: Implement spec validation, defaults are grabbed above.
        """
        if not isinstance(val, str) or val is None:
            return val
        if val.lower() == "true":
            return True
        if val.lower() == "false":
            return False
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            pass
        return val


    def on_skip(self, input):
        """
        Hook for when a step is skipped.

        Args:
            input (str | LigerIRISDataModel):
        """
        self.status = "SKIPPED"
