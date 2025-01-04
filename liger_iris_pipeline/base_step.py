
from functools import wraps
import warnings
import os

from stpipe import Step
from stpipe import config_parser
from . import datamodels
from . import __version__

from jwst.lib.suffix import remove_suffix
from stpipe import crds_client

__all__ = [
    "LigerIRISStep"
]

class LigerIRISStep(Step):

    # NOTE: This is kind of a hack, change if possible
    spec = """
        output_ext = string(default='.fits')  # Output file type
    """

    @classmethod
    def call(cls, *args, return_step : bool = False, **kwargs):
        """
        Hack to allow the pipeline to return the step or pipeline object that is created
        """
        filename = None
        if len(args) > 0:
            filename = args[0]
        config, config_file = cls.build_config(filename, **kwargs)

        if "class" in config:
            del config["class"]

        if "logcfg" in config:
            try:
                self.log.load_configuration(config["logcfg"])
            except Exception as e:
                raise RuntimeError(
                    f"Error parsing logging config {config['logcfg']}"
                ) from e
            del config["logcfg"]

        name = config.get("name", None)
        instance = cls.from_config_section(config, name=name, config_file=config_file)

        result = instance.run(*args)

        if return_step:
            return result, instance
        else:
            return result


    @classmethod
    def _datamodels_open(cls, init, **kwargs):
        return datamodels.open(init, **kwargs)

    def finalize_result(self, result, reference_files_used):
        if isinstance(result, datamodels.LigerIRISDataModel):
            result.meta.calibration_software_revision = __version__

            if len(reference_files_used) > 0:
                for ref_name, filename in reference_files_used:
                    if hasattr(result.meta.ref_file, ref_name):
                        getattr(result.meta.ref_file, ref_name).name = filename
                result.meta.ref_file.crds.sw_version = crds_client.get_svn_version()
                result.meta.ref_file.crds.context_used = crds_client.get_context_used(result.crds_observatory)
                if self.parent is None:
                    self.log.info(f"Results used CRDS context: {result.meta.ref_file.crds.context_used}")


    def remove_suffix(self, name):
        return remove_suffix(name)

    @wraps(Step.run)
    def run(self, *args, **kwargs):
        result = super().run(*args, **kwargs)
        if not self.parent:
            self.log.info(f"Results used liger_iris_pipeline version: {__version__}")
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
    
    @classmethod
    def build_config(cls, input, **kwargs):  # noqa: A002
        """
        Build the ConfigObj to initialize a Step.
        This does not call out to CRDS top determine the appropriate config.

        A Step config is built in the following order:
        - Local parameter reference file
        - Step keyword arguments

        Parameters
        ----------
        input : str or None
            Input file

        kwargs : dict
            Keyword arguments that specify Step parameters.

        Returns
        -------
        config, config_file : ConfigObj, str
            The configuration and the config filename.
        """
        config = config_parser.ConfigObj()

        if "config_file" in kwargs:
            config_file = kwargs["config_file"]
            del kwargs["config_file"]
            config_from_file = config_parser.load_config_file(str(config_file))
            config_parser.merge_config(config, config_from_file)
            config_dir = os.path.dirname(config_file)
        else:
            config_file = None
            config_dir = ""

        config_kwargs = config_parser.ConfigObj()

        # load and merge configuration files for each step they are provided:
        steps = {}
        if "steps" in kwargs:
            for step, pars in kwargs["steps"].items():
                if "config_file" in pars:
                    step_config_file = os.path.join(config_dir, pars["config_file"])
                    cfgd = config_parser.load_config_file(step_config_file)
                    if "name" in cfgd:
                        if cfgd["name"] != step:
                            raise ValueError(
                                "Step name from configuration file "
                                f"'{step_config_file}' does not match step "
                                "name in the 'steps' argument."
                            )
                        del cfgd["name"]
                    cfgd.pop("class", None)
                    cfgd.update(pars)
                    steps[step] = cfgd
                else:
                    steps[step] = pars

            kwargs = {k: v for k, v in kwargs.items() if k != "steps"}
            if steps:
                kwargs["steps"] = steps

        config_parser.merge_config(config_kwargs, kwargs)
        config_parser.merge_config(config, config_kwargs)

        return config, config_file