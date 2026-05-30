from .model_base import CalibrationModel
from .mixins import DefaultDQMixin

__all__ = ['NonlinearCorrectionModel']


class NonlinearCorrectionModel(DefaultDQMixin, CalibrationModel):
    """
    Class for nonlinearity correction reference files.

    Extensions
    ----------

    HDU Name       HDU Type  Data Type  Dimensions        Units  Description
    --------       --------  ---------  ----------        -----  -------------------------
    COEFFS         Image     Float64    Ny x Nx x Ncoeff  None   Nonlinearity coefficients
    COEFFS_ERR     Image     Float64    Ny x Nx x Ncoeff  None   Uncertainties on coefficients
    NONLIN_THRESH  Image     UInt16     Ny x Nx           DN     Nonlinearity threshold
    NONLIN_MAX     Image     UInt16     Ny x Nx           DN     Nonlinearity maximum
    DQ             Image     UInt32     Ny x Nx           None   Data quality flags
    """
    schema_url = "https://oirlab.github.io/schemas/NonlinearCorrectionModel.schema"
    _cal_type = "nonlin"

    def get_primary_array_name(self):
        return 'coeffs'