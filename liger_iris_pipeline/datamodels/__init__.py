from .model_base import *
from .utils import *
from .ramp import *
from .imager import *
from .nonlin import *
from .dark import *
from .detector_flat import *
from .ifs import *
from .dq import *
from .distortion_map import *
from .read_noise import *
from .saturation import *
from .gain import *
from .bias import *
from .dqflags import *

# Instrument config
from .liger_config import LigerConfig
from .iris_config import IRISConfig
INSTRUMENT_CONFIGS = {
    'Liger' : LigerConfig,
    'IRIS'  : IRISConfig
}

_local_dict = locals()
DEFINED_MODELS = {name : _local_dict[name] for name in _local_dict if name.endswith('Model')}