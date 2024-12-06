from .model_base import LigerIRISDataModel
from .ramp import RampModel
from .imager import ImagerModel
from .referencefile import ReferenceFileModel
from .dark import DarkModel
from .flat import FlatModel
from .ifu import IFUImageModel, IFUCubeModel
from .dq import DQModel

from .container import ModelContainer

from .utils import open


__all__ = [
    "LigerIRISDataModel",
    "RampModel",
    "ImagerModel",
    "DEFINED_MODELS",
    "ReferenceFileModel",
    "DarkModel", "FlatModel",
    "IFUImageModel", "IFUCubeModel",
    "DQModel",
    "ModelContainer",
    "open"
]

_local_dict = locals()
DEFINED_MODELS = {name : _local_dict[name] for name in __all__ if "Model" in name}