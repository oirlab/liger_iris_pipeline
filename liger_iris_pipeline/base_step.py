
from functools import wraps
from collections.abc import Sequence
import warnings
import copy
import gc

import stpipe.utilities
from . import datamodels
from astropy.io import fits
from pathlib import Path
import stpipe.log
import os
from typing import Self
import yaml

import stpipe
from stpipe import cmdline
from stpipe import Step
from stpipe import config_parser
from . import datamodels
from . import __version__

from stpipe import crds_client

__all__ = [
    "LigerIRISStep"
]

class LigerIRISStep(Step):

    exclude_spec = [
        "pre_hooks", "post_hooks",
        "output_use_index", "output_use_model",
        "suffix", "search_output_file", "input_dir", 'output_ext',
        'steps' # Make spec only contain config for THIS class, not substeps
    ]

    #spec = """
    #    output_dir = str(default=None) # Directory path for output files
    #"""

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

        # TODO: Refactor this back into stpipe Step classmethods.

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

    def process(self, *args, **kwargs):
        """
        This is where real work happens. Every Step subclass has to
        override this method. The default behaviour is to raise a
        NotImplementedError exception.
        """
        raise NotImplementedError(f"Class {self.__class__} does not implement instance method `process`.")

    # @classmethod
    # def call(cls, input, return_step : bool = False, config_file : str | None = None, **kwargs):
    #     """
    #     Override call so the Pipeline or Step instance is optionally returned.
        
    #     Parameters:
    #         input (str | LigerIRISDataModel | list[str] | list[LigerIRISDataModel]):
    #             1. filename of datamodel
    #             2. filename of ASN
    #             3. datamodel
    #             4. list of filenames
    #             5. list of datamodels
    #     """
    #     instance = cls(config_file=config_file)
    #     result = instance.run(input, **kwargs)

    #     if return_step:
    #         return result, instance
    #     else:
    #         return result


    @classmethod
    def _datamodels_open(cls, init, **kwargs):
        return datamodels.open(init, **kwargs)

    def finalize_result(self, result : datamodels.LigerIRISDataModel, reference_files_used : dict[str, str]):
        result.meta.drs_version = __version__
        from .pipeline import LigerIRISPipeline
        if not isinstance(self, LigerIRISPipeline):
            if hasattr(result.meta.drs_step, f"{self.class_alias}"):
                setattr(result.meta.drs_step, f"{self.class_alias}", self.status)
            else:
                self.log.warning(f"Could not update status for {result.meta.drs_step}.{self.class_alias} in datamodel.")

        # Set references files used
        if len(reference_files_used) > 0:
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
            output_dir : str | None = None
        ):
        """
        Saves the given model using the step/pipeline's naming scheme.
        """
        if output_path:
            output_path = model.save(output_path)
        else:
            if output_dir is None:
                output_dir = self.output_dir
            output_path = self.make_output_path(model, output_dir=self.output_dir)
            output_path = model.save(output_path)
        self.log.info(f"Saved model in {output_path}")

        return output_path
    
    def run(self, input, *args, **kwargs):
        """
        Run handles the generic setup and teardown that happens with the running of each step.
        The real work that is unique to each step type is done in the `process` method.

        Args:
            input (str | LigerIRISDataModel | list[str] | list[LigerIRISDataModel]):
                    1. filename of datamodel
                    2. filename of ASN
                    3. datamodel
                    4. ASN
                    5. list of filenames
                    6. list of datamodels
        Returns:
            result (LigerIRISDataModel | list[LigerIRISDataModel] | list[LigerIRISDataModel]):
                The result(s) of the step. Steps can only return a single model, but Pipelines can return a list.
        """
        gc.collect()
        with stpipe.log.record_logs(formatter=self._log_records_formatter) as log_records:
            self._log_records = log_records

            # Make generic log messages go to this step's logger
            orig_log = stpipe.log.delegator.log
            stpipe.log.delegator.log = self.log

            step_result = None

            # log Step or Pipeline parameters from top level only
            if self.parent is None:
                self.log.info(
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
            
            # Main try block
            try:

                # Update the params based on kwargs
                pars = self.get_pars()
                kwargs_process = copy.deepcopy(kwargs)
                for k, v in kwargs.items():
                    if k in pars:
                        setattr(self, k, v)
                        del kwargs_process[k] # Remaining are for process

                # Prefetch references
                self._reference_files_used = []
                if not self.skip and self.prefetch_references:
                    self.prefetch(input)

                # Call process and catch signature error
                if not self.skip:
                    try:
                        step_result = self.process(input, *args, **kwargs_process)
                    except TypeError as e:
                        if "process() takes exactly" in str(e):
                            raise TypeError(
                                "Incorrect number of arguments to step"
                            ) from e
                        raise
                else:
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
    
    @staticmethod
    def _make_output_path(step : Self, model : datamodels.LigerIRISDataModel, output_dir : str | None):
        """
        Generate the output path for the given model.
        """
        if output_dir is None:
            if step.output_dir is not None:
                output_dir = step.output_dir
            elif model._filename is not None:
                output_dir = os.path.split(os.path.abspath(model._filename))[0]
            else:
                raise ValueError("No output directory provided and no default found.")
        output_filename = model.generate_filename()
        output_path = os.path.join(output_dir, output_filename)

        return output_path

    @classmethod
    def load_spec_file(cls, preserve_comments=stpipe.utilities._not_set):
        spec = super().load_spec_file(preserve_comments=preserve_comments)
        for k in cls.exclude_spec:
            if k in spec:
                del spec[k]
        return spec
    
    def get_pars(self, full_spec=True):
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