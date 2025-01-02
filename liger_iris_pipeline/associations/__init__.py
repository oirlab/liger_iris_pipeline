# https://jwst-pipeline.readthedocs.io/en/latest/jwst/associations/association_reference.html#ref-asn-core-methods

from .association_base import LigerIRISAssociation
from .iris_imager_level0 import IRISImagerL0Association
from .iris_imager_level1 import IRISImagerL1Association
from .utils import load_asn

__all__ = [
    "LigerIRISAssociation",
    "IRISImagerL0Association",
    "IRISImagerL1Association",
    "load_asn"
]

_local_dict = locals()
DEFINED_ASSOCIATIONS = {name : _local_dict[name] for name in __all__ if "Association" in name}