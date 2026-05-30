import importlib.resources
import os
import yaml
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConfigFile:
    name: str
    filepath: str
    class_: str
    extra : dict[str, Any] = field(default_factory=dict)

    def __init__(self, name: str, filepath: str, class_: str | type, **kwargs: Any):
        self.name = name
        self.filepath = os.path.abspath(filepath)
        if isinstance(class_, type):
            class_ = class_.__name__
        self.class_ = class_

        extra = kwargs.pop("extra", {})
        if extra is None:
            extra = {}

        if not isinstance(extra, dict):
            raise TypeError("'extra' must be a dict")

        self.extra = {**extra, **kwargs}

        self.extra.setdefault("quicklook", False)

        if type(self.extra["quicklook"]) is not bool:
            raise ValueError(
                f"Invalid value for 'quicklook' in config '{self.name}': "
                f"{self.extra['quicklook']}. Must be a boolean."
            )

    @property
    def filename(self):
        return os.path.basename(self.filepath)
        
    def __getattr__(self, item):
        if item in self.extra:
            return self.extra[item]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{item}'")


class ConfigLibrary:
    
    def __init__(self):
        self.configs = {}

    def populate(self):
        config_dir = self.get_config_dir()
        for filename in os.listdir(config_dir):
            if filename.endswith(('.yaml', '.yml')):
                config_filepath = os.path.join(config_dir, filename)
                config_data = self._load(config_filepath)
                self.configs[config_data['name']] = ConfigFile(
                    name=config_data['name'],
                    filepath=config_filepath,
                    class_=config_data['class'],
                    quicklook=config_data.get('quicklook', False)
                )
        return self.configs

    def get_config_filepath(self, config_name : str):
        """
        Retrieve a config filepath by name.

        Parameters
        ----------
        config_name : str
            The name of the config file to retrieve (with or without extension).

        Returns
        -------
        config : str
        """
        if config_name in self.configs:
            return os.path.join(
                self.get_config_dir(),
                self.configs[config_name].filename
            )
        raise KeyError(f"Config '{config_name}' not found in library.")

    def get_config_dir(self):
        config_path = importlib.resources.files("liger_iris_pipeline").joinpath("configs")
        return str(config_path)

    def __enter__(self):
        self.populate()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        del self.configs

    def __contains__(self, config_name : str):
        return config_name in self.configs
    
    @staticmethod
    def _load(config_filepath : str):
        with open(config_filepath, 'r') as f:
            return yaml.safe_load(f)

    def load(self, config_name : str):
        if config_name in self.configs:
            return self._load(
                os.path.join(
                    self.get_config_dir(),
                    self.configs[config_name].filename
                )
            )
        raise KeyError(f"Config '{config_name}' not found in library.")

