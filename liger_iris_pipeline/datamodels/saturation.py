from .model_base import CalibrationModel
from .mixins import DefaultDQMixin

__all__ = ['SaturationModel']


class SaturationModel(DefaultDQMixin, CalibrationModel):
    """
    Class for saturation reference files.

    Extensions
    ----------

    HDU Name    HDU Type  Data Type  Dimensions  Units  Description
    --------    --------  ---------  ----------  -----  --------------------
    SAT_THRESH  Image     UInt16     Ny x Nx     DN     Saturation threshold
    DQ          Image     UInt32     Ny x Nx     None   Data quality flags
    """
    schema_url = "https://oirlab.github.io/schemas/SaturationModel.schema"
    _cal_type = "saturation"

    def get_primary_array_name(self):
        return 'sat_thresh'