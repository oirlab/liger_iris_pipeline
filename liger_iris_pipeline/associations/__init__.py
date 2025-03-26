# https://jwst-pipeline.readthedocs.io/en/latest/jwst/associations/association_reference.html#ref-asn-core-methods

from .association_base import LigerIRISAssociation, L0Association, L1Association, L2Association
from .utils import load_asn

__all__ = [
    "LigerIRISAssociation",
    "L0Association",
    "L1Association",
    "L2Association",
    "load_asn"
]

_local_dict = locals()
DEFINED_ASSOCIATIONS = {name : _local_dict[name] for name in __all__ if "Association" in name}