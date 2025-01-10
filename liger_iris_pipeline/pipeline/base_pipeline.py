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

    default_association : LigerIRISAssociation = None

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
        
    def input_to_asn(self, input):
        """
        Convert input to an association.

        Parameters:
            input (str | Path | LigerIRISAssociation): The input file.

        Returns:
            LigerIRISAssociation: An instance of the appropriate LigerIRISAssociation.
        """

        # Input already is an association
        if isinstance(input, LigerIRISAssociation):
            return input
        
        # Input is a file
        if isinstance(input, str | Path):
            input = str(input)
            if os.path.splitext(input)[1] == '.json': # Association file
                asn = load_asn(input)
            else:
                asn = self.default_association.from_member(input) # DataModel file
        elif isinstance(input, datamodels.LigerIRISDataModel):
            asn = self.default_association.from_member(input)
        elif isinstance(input, dict):
            asn = self.default_association.from_product(input) # Single product (dict):
        else:
            raise ValueError(f"Input type {type(input)} not supported.")
        
        return asn
    
    @staticmethod
    def asn_product_by_types(exp_product : dict):
        """
        Get the members of an exposure product by type.

        Parameters:
            exp_product (dict): The exposure product.

        Returns:
            dict: The members of the exposure product by type.
        """
        members_by_type = defaultdict(list)
        for member in exp_product["members"]:
            members_by_type[member["exptype"].lower()].append(member["expname"])
        return members_by_type