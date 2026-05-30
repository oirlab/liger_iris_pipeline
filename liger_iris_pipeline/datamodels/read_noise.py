from .model_base import CalibrationModel
from .mixins import DefaultDQMixin

__all__ = ['ReadNoiseModel']


class ReadNoiseModel(DefaultDQMixin, CalibrationModel):
    """
    Class for read noise reference files.

    Extensions
    ----------

    HDU Name      HDU Type  Data Type  Dimensions  Units  Description
    --------      --------  ---------  ----------  -----  ------------------
    RN            Image     Float32    Ny x Nx     e-     Read noise data
    RN_ERR        Image     Float32    Ny x Nx     e-     Read noise error
    DQ            Image     UInt32     Ny x Nx     None   Data quality flags
    """
    schema_url = "https://oirlab.github.io/schemas/ReadNoiseModel.schema"
    _cal_type = "rn"

    def get_primary_array_name(self):
        """
        Returns the name "primary" array for this model, which
        controls the size of other arrays that are implicitly created.
        This is intended to be overridden in the subclasses if the
        primary array's name is not "data".
        """
        return 'rn'