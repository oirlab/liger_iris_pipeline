from .model_base import CalibrationModel
from .mixins import DefaultDQMixin

__all__ = ['DistortionMapModel']


class DistortionMapModel(DefaultDQMixin, CalibrationModel):
    """
    Class for distortion map reference files.

    Extensions
    ----------

    HDU Name  HDU Type  Data Type  Dimensions  Units   Description
    --------  --------  ---------  ----------  -----   -------------------------
    DX        Image     Float32    Ny x Nx     pixels  X-displacement correction
    DY        Image     Float32    Ny x Nx     pixels  Y-displacement correction
    DX_ERR    Image     Float32    Ny x Nx     pixels  X-displacement error
    DY_ERR    Image     Float32    Ny x Nx     pixels  Y-displacement error
    DQ        Image     UInt32     Ny x Nx     None    Data quality flags
    """
    schema_url = "https://oirlab.github.io/schemas/DistortionMapModel.schema"
    _cal_type = "distortion"