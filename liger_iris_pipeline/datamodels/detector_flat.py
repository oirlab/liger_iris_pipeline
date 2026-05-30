from .model_base import CalibrationModel
from .mixins import DefaultDQMixin, DefaultErrMixin

__all__ = ['DetectorFlatModel']


class DetectorFlatModel(DefaultErrMixin, DefaultDQMixin, CalibrationModel):
    """
    Class for detector flat reference files.

    Extensions
    ----------

    HDU Name     HDU Type  Data Type  Dimensions  Units  Description
    --------     --------  ---------  ----------  -----  ----------------------------
    DATA         Image     Float32    Ny x Nx     e-/s   Detector flat data
    ERR          Image     Float32    Ny x Nx     e-/s   Detector flat error
    VAR_POISSON  Image     Float32    Ny x Nx     None   2-D Poisson variance array
    VAR_RNOISE   Image     Float32    Ny x Nx     None   2-D read noise variance array
    DQ           Image     UInt32     Ny x Nx     None   Data quality flags
    """
    schema_url = "https://oirlab.github.io/schemas/DetectorFlatModel.schema"
    _cal_type = "detflat"

    def on_init(self, init):
        super().on_init(init)
        self.meta.exposure.type = 'DETFLAT'