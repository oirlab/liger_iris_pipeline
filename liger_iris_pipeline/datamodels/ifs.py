from .model_base import LigerIRISDataModel
from .mixins import DefaultErrMixin, DefaultDQMixin
from liger_iris_pipeline.datamodels.meta_utils import set_default_ifs_wcs_meta


__all__ = ['IFSImageModel', 'IFSCubeModel']

class _IFSBase(DefaultErrMixin, DefaultDQMixin, LigerIRISDataModel):
    """
    Base class for IFS data models.
    Not intended to be instantiated directly.
    """

    def on_init(self, init):
        if self.meta.instrument.mode is None:
            self.meta.instrument.mode = 'IFS'
        set_default_ifs_wcs_meta(self)
        super().on_init(init)

class IFSImageModel(_IFSBase):
    """
    Class for 2-D IFS image data (level 1).

    Extensions
    ----------

    HDU Name     HDU Type  Data Type  Dimensions  Units  Description
    --------     --------  ---------  ----------  -----  ----------------------------
    DATA         Image     Float32    Ny x Nx     e-/s   2-D science data image
    ERR          Image     Float32    Ny x Nx     e-/s   2-D error image
    VAR_POISSON  Image     Float32    Ny x Nx     None   2-D Poisson variance array
    VAR_RNOISE   Image     Float32    Ny x Nx     None   2-D read noise variance array
    DQ           Image     UInt32     Ny x Nx     None   2-D data quality array
    """
    schema_url = "https://oirlab.github.io/schemas/IFSImageModel.schema"


class IFSCubeModel(_IFSBase):
    """
    Class for 3-D IFS cube data (level >= 2).

    Extensions
    ----------

    HDU Name     HDU Type  Data Type  Dimensions       Units   Description
    --------     --------  ---------  ----------       -----   --------------------------
    DATA         Image     Float32    Nwave x Ny x Nx  e-/s    3-D science data cube
    ERR          Image     Float32    Nwave x Ny x Nx  e-/s    3-D error cube
    VAR_POISSON  Image     Float32    Nwave x Ny x Nx  None    3-D Poisson variance cube
    VAR_RNOISE   Image     Float32    Nwave x Ny x Nx  None    3-D read noise variance cube
    DQ           Image     UInt32     Nwave x Ny x Nx  None    3-D data quality cube
    WAVELENGTH   Image     Float32    Nwave            micron  1-D wavelength array
    """
    schema_url = "https://oirlab.github.io/schemas/IFSCubeModel.schema"