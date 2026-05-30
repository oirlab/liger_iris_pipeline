import yaml
import numpy as np
import warnings

from .datamodels import LigerIRISDataModel

# Representer functions for custom data types for YAML serialization.
# As of stpipe v0.11.1, Numpy datatypes and datamodels are not correctly serialized.

def _numpy_representer(dumper, data):
    return dumper.represent_data(data.item())

def _datamodel_representer(dumper, data):
    """Represent LigerIRISDataModel using its repr() string."""
    return dumper.represent_str(repr(data))

def register_datatypes_yaml():
    """Register custom YAML representers for numpy types and datamodels."""
    numpy_types = [
        # Floating point types
        np.float16, np.float32, np.float64,
        
        # Signed integer types
        np.int8, np.int16, np.int32, np.int64,
        np.byte, np.short, np.intc, np.int_, np.longlong,
        
        # Unsigned integer types
        np.uint8, np.uint16, np.uint32, np.uint64,
        np.ubyte, np.ushort, np.uintc, np.uint, np.ulonglong,
        
        # Boolean
        np.bool_,
        
        # Complex types
        np.complex64, np.complex128,
        np.clongdouble,
    ]
    
    for np_type in numpy_types:
        try:
            yaml.add_representer(np_type, _numpy_representer)
            yaml.add_representer(np_type, _numpy_representer, Dumper=yaml.SafeDumper)
        except AttributeError:
            warnings.warn(f"Could not add YAML representer for numpy type: {np_type}")

    # Also register DataModels
    try:
        yaml.add_multi_representer(LigerIRISDataModel, _datamodel_representer)
        yaml.add_multi_representer(LigerIRISDataModel, _datamodel_representer, Dumper=yaml.SafeDumper)
    except Exception as e:
        warnings.warn(f"Could not add YAML representer for LigerIRISDataModel: {e}")

register_datatypes_yaml()