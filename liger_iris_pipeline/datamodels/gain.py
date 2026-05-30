from .model_base import CalibrationModel
from .mixins import DefaultDQMixin

__all__ = ['GainModel']


class GainModel(DefaultDQMixin, CalibrationModel):
    """
    Class for gain reference files.

    Extensions
    ----------

    HDU Name  HDU Type  Data Type  Dimensions          Units  Description
    --------  --------  ---------  ----------          -----  -----------
    GAIN      Image     Float32    Ny x Nx             e-/DN  Gain data
    RN        Image     Float32    Ny x Nx             e-/DN  Read noise
    COV       Image     Float32    Ny x Nx x Ny x Nx   None   4-D gain covariance array
    DQ        Image     UInt32     Ny x Nx             None   Data quality flags
    """
    schema_url = "https://oirlab.github.io/schemas/GainModel.schema"
    _cal_type = "gain"

    def get_primary_array_name(self):
        """
        Returns the name "primary" array for this model, which
        controls the size of other arrays that are implicitly created.
        This is intended to be overridden in the subclasses if the
        primary array's name is not "data".
        """
        return 'gain'