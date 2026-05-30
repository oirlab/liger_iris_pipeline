from .model_base import CalibrationModel
from .mixins import DefaultDQMixin

__all__ = ['DQModel']

# NOTE: Does DQModel inherit from DefaultDQMixin?
class DQModel(DefaultDQMixin, CalibrationModel):
    """
    Class for data quality (DQ) reference files.

    Extensions
    ----------

    HDU Name  HDU Type  Data Type  Dimensions  Units  Description
    --------  --------  ---------  ----------  -----  ------------------
    DQ        Image     UInt32     Ny x Nx     None   Data quality flags
    """
    schema_url = "https://oirlab.github.io/schemas/DQModel.schema"
    _cal_type = "dq"

    def get_primary_array_name(self):
        """
        Returns the name "primary" array for this model, which
        controls the size of other arrays that are implicitly created.
        This is intended to be overridden in the subclasses if the
        primary array's name is not "data".
        """
        return 'dq'