import os
from collections import defaultdict

from stpipe import Pipeline
from .. import datamodels
from ..base_step import LigerIRISStep
from pathlib import Path
import stpipe
from ..associations import LigerIRISAssociation, load_asn

from stpipe import config_parser

__all__ = [
    "LigerIRISPipeline"
]

class LigerIRISPipeline(LigerIRISStep, Pipeline):

    #default_association : LigerIRISAssociation = None

    def __init__(self, config_file : str | None = None, **kwargs):
        """
        Create a LigerIRISPipeline instance.
        Configuration is determined according to:
            1. Class's spec object
            2. config_file
            3. kwargs
        """
        self._reference_files_used = []
        self.init_logger()

        # Load config for this Pipeline.
        self.config_file = config_file
        if self.config_file is not None:
            config = config_parser.load_config_file(config_file)
        else:
            config = config_parser.ConfigObj()

        # Load any subconfig files to load
        if "steps" in config:
            root_dir = os.path.dirname(self.config_file or "")
            for step_alias, step_config in config["steps"].items():
                if "config_file" in step_config:
                    step_config = config_parser.load_config_file(os.path.join(root_dir, step_config["config_file"]))
                    config["steps"][step_alias].merge(step_config)
        else:
            config["steps"] = {}

        # Parse the config from the spec and any provided kwargs
        pipeline_spec = self.load_spec_file()
        pipeline_kwargs = config_parser.config_from_dict(
            kwargs,
            pipeline_spec,
            root_dir=None,
            allow_missing=False
        )
        pipeline_kwargs.update(config)
        config = pipeline_kwargs

        # Initilize the steps and their config
        self.init_steps(config)

        # Merge the spec with the config
        # TODO: MERGE THIS WITH BELOW
        pars = self.get_pars()
        for k, v in kwargs.items():
            if k in pars:
                config[k] = v

        # Set the pipeline level config parameters as member variables
        for key, val in config.items():
            if key not in ("class", "steps", "config_file"):
                _val = self.parse_config_kwarg(key, val, pipeline_spec)
                setattr(self, key, _val)
        

    def init_steps(self, config : config_parser.ConfigObj):
        if self.config_file is not None:
            config_dir = os.path.dirname(self.config_file)
        else:
            config_dir = ""
        for step_alias, _class in self.step_defs.items():
            if step_alias not in config["steps"]:
                config["steps"][step_alias] = {}
            step_config = config["steps"][step_alias]
            if "config_file" in step_config:
                step_config_file = os.path.join(config_dir, step_config["config_file"])
            else:
                step_config_file = None
            step_kwargs = {}
            if step_config_file is not None:
                step_config = config_parser.load_config_file(config_file=step_config_file)
                step_kwargs.update(step_kwargs)
            for key, val in step_config.items():
                if key not in ('class', 'config_file'):
                    step_kwargs[key] = val
            new_step = _class(
                config_file=step_config_file,
                **step_kwargs
            )
            setattr(self, step_alias, new_step)
    

    # @classmethod
    # def load_spec_file(cls, preserve_comments=_not_set):
    #     spec = config_parser.get_merged_spec_file(
    #         cls, preserve_comments=preserve_comments
    #     )

    #     spec["steps"] = Section(spec, spec.depth + 1, spec.main, name="steps")
    #     steps = spec["steps"]
    #     for key, val in cls.step_defs.items():
    #         if not issubclass(val, Step):
    #             raise TypeError(f"Entry {key!r} in step_defs is not a Step subclass")
    #         stepspec = val.load_spec_file(preserve_comments=preserve_comments)
    #         steps[key] = Section(steps, steps.depth + 1, steps.main, name=key)

    #         config_parser.merge_config(steps[key], stepspec)

    #         # Also add a key that can be used to specify an external
    #         # config_file
    #         step = spec["steps"][key]
    #         step["config_file"] = "string(default=None)"
    #         step["name"] = "string(default='')"
    #         step["class"] = "string(default='')"

    #     return spec