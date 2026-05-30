import importlib
import os


__all__ = ['get_config_path']


def get_config_path(config_file : str) -> str:
    """
    Resolve the path to a configuration file.

    Parameters
    ----------
    config_file : str
        The base filename of the configuration file or a valid file path.

    Returns
    -------
    str
        The resolved path to the configuration file.
    """
    if os.path.isfile(config_file):
        return config_file

    config_dir = _get_config_dir()
    candidate = os.path.join(config_dir, config_file)
    if os.path.isfile(candidate):
        return candidate
    raise FileNotFoundError(f"No valid config file found for: {config_file}")


def _get_config_dir():
    config_dir = importlib.resources.files("liger_iris_pipeline.configs")
    if config_dir.is_dir():
        return str(config_dir)
    else:
        raise FileNotFoundError("Config directory not found in liger_iris_pipeline.configs")


def resolve_step_class(name: str):
    """
    Resolve a step class name to its actual class.
    
    Parameters
    ----------
    name : str
        The name of the step class, optionally including module path.
        
    Returns
    -------
    type or None
        The resolved class or None if not found
    """
    def _try_import(module_path, class_name):
        try:
            module = importlib.import_module(module_path)
            return getattr(module, class_name, None)
        except (ImportError, AttributeError):
            return None

    # Check if name contains a module path
    if '.' in name:
        module_path, class_name = name.rsplit('.', 1)
        resolved_class = _try_import(module_path, class_name)
        if resolved_class:
            return resolved_class
    else:
        # If no module path, get the top-level module
        top_level_module = __name__.split('.')[0]

        # Try resolving the class in the top-level module with suffixes
        resolved_class = _try_import(top_level_module, name)
        if resolved_class:
            return resolved_class

    # Class not found
    return None

# def init_step_from_config(config : dict | str, **kwargs):
#     """
#     Create an instance of a primitive from a configuration dictionary or file.

#     Parameters
#     ----------
#     config : dict | str | None
#         A configuration dictionary, or the path to to a configuration file.
#     **kwargs
#         Any additional keyword arguments to set or override for the primitive or pipeline.

#     Returns
#     -------
#     ProcessingComponent
#         An instance of the requested primitive.
#     """
#     if isinstance(config, str):
#         config = get_config_path(config)
#         config = read_config_file(config)
#     _class = resolve_primitive_class(config['class'])
#     return _class(config=config, **kwargs) 