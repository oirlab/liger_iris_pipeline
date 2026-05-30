from .model_base import LigerIRISDataModel
from .mixins import DefaultErrMixin, DefaultDQMixin, DefaultSubarrayMapMixin

from .meta_utils import set_default_imager_wcs_meta

__all__ = ['ImagerModel']


class ImagerModel(DefaultErrMixin, DefaultDQMixin, DefaultSubarrayMapMixin, LigerIRISDataModel):
    """
    Class for 2-D imager data.

    Extensions
    ----------

    HDU Name      HDU Type  Data Type  Dimensions  Units  Description
    --------      --------  ---------  ----------  -----  ----------------------------
    DATA          Image     Float32    Ny x Nx     e-/s   2-D science data array
    ERR           Image     Float32    Ny x Nx     e-/s   2-D error array
    VAR_POISSON   Image     Float32    Ny x Nx     None   2-D Poisson variance array
    VAR_RNOISE    Image     Float32    Ny x Nx     None   2-D read noise variance array
    DQ            Image     UInt32     Ny x Nx     None   2-D data quality array
    SUBARRAY_MAP  Image     UInt8      Ny x Nx     None   Subarray map
    """
    schema_url = "https://oirlab.github.io/schemas/ImagerModel.schema"

    def on_init(self, init):
        if self.meta.instrument.mode is None:
            self.meta.instrument.mode = 'IMG'
        set_default_imager_wcs_meta(self)
        super().on_init(init)

        # if self.err is None:
        #     self.err = self.get_default('err')
        # if self.var_rnoise is None:
        #     self.var_rnoise = self.get_default('var_rnoise')
        # if self.var_poisson is None:
        #     self.var_poisson = self.get_default('var_poisson')
        # if self.dq is None:
        #     self.dq = self.get_default('dq')