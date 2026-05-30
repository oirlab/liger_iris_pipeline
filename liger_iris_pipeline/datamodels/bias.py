from .model_base import CalibrationModel
from .mixins import DefaultDQMixin, DefaultErrMixin

__all__ = ['BiasModel']


class BiasModel(DefaultErrMixin, DefaultDQMixin, CalibrationModel):
    """
    Class for bias reference files.

    Extensions
    ----------

    HDU Name  HDU Type  Data Type  Dimensions  Units  Description
    --------  --------  ---------  ----------  -----  -----------
    DATA      Image     Float32    Ny x Nx     DN     Bias level
    ERR       Image     Float32    Ny x Nx     DN     Bias error
    DQ        Image     UInt32     Ny x Nx     None   Data quality
    """
    schema_url = "https://oirlab.github.io/schemas/BiasModel.schema"
    _cal_type = "bias"