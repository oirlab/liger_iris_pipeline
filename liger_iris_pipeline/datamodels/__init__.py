from .model_base import *
from .utils import *
from .ramp import *
from .imager import *
from .nonlin import *
from .referencefile import *
from .dark import *
from .flat import *
from .ifu import *
from .dq import *

_local_dict = locals()
DEFINED_MODELS = {name : _local_dict[name] for name in _local_dict if name.endswith('Model')}