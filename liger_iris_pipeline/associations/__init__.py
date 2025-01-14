# https://jwst-pipeline.readthedocs.io/en/latest/jwst/associations/association_reference.html#ref-asn-core-methods

from .association_base import LigerIRISAssociation
from .level0 import L0Association
from .level1 import L1Association
from .subarray import SubarrayAssociation
from .utils import load_asn

__all__ = [
    "LigerIRISAssociation",
    "L0Association",
    "L1Association",
    "SubarrayAssociation",
    "load_asn"
]

_local_dict = locals()
DEFINED_ASSOCIATIONS = {name : _local_dict[name] for name in __all__ if "Association" in name}