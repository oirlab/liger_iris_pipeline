from astropy.io import registry

from .cube import CubeModel
from .model_base import LigerIrisDataModel
from .liger_iris_image import LigerIrisImageModel
from .ramp import RampModel
from .mask import MaskModel
from .flat import FlatModel
from .dark import DarkModel
from .reference import (
    ReferenceImageModel,
    ReferenceCubeModel,
    ReferenceQuadModel,
    ReferenceFileModel,
)


__all__ = [
    "CubeModel",
    "LigerIrisDataModel",
    "LigerIrisImageModel",
    "RampModel",
    "MaskModel",
    "ReferenceImageModel",
    "FlatModel",
    "DarkModel",
    "ReferenceCubeModel",
    "ReferenceQuadModel",
    "ReferenceFileModel",
]

_all_models = __all__
_local_dict = locals()
_defined_models = {k: _local_dict[k] for k in _all_models}

def monkeypatch_jwst_datamodels():
    import stdatamodels.jwst.datamodels

    stdatamodels.jwst.datamodels._defined_models.update(_defined_models)

    # Current ModelContainer is hardcoded to "jwst"
    from jwst.datamodels import ModelContainer
    ModelContainer.crds_observatory = property(lambda self : self[0].crds_observatory if len(self) > 0 else "ligeriri")
