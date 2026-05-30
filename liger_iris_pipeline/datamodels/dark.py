from .model_base import CalibrationModel
from .mixins import DefaultDQMixin, DefaultErrMixin

__all__ = ['DarkModel']

class DarkModel(DefaultErrMixin, DefaultDQMixin, CalibrationModel):
    """
    Class for dark reference files.

    Extensions
    ----------

    HDU Name     HDU Type  Data Type  Dimensions  Units     Description
    --------     --------  ---------  ----------  -----     -----------
    DATA         Image     Float32    Ny x Nx     DN/s      Dark current data.
    ERR          Image     Float32    Ny x Nx     DN/s      Dark current error.
    VAR_POISSON  Image     Float32    Ny x Nx     (DN/s)^2  Dark current variance (Poisson).
    VAR_RNOISE   Image     Float32    Ny x Nx     (DN/s)^2  Dark current variance (read noise).
    DQ           Image     UInt32     Ny x Nx     None      Data quality.
    """
    schema_url = "https://oirlab.github.io/schemas/DarkModel.schema"
    _cal_type = "dark"

    def on_init(self, init):
        super().on_init(init)
        self.meta.exposure.type = 'DARK'

        if self.err is None:
            self.err = self.get_default('err')
        if self.var_rnoise is None:
            self.var_rnoise = self.get_default('var_rnoise')
        if self.var_poisson is None:
            self.var_poisson = self.get_default('var_poisson')
        if self.dq is None:
            self.dq = self.get_default('dq')



