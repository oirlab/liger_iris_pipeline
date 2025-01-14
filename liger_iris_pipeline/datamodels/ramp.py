from .model_base import LigerIRISDataModel


__all__ = ['RampModel']


class RampModel(LigerIRISDataModel):
    """
    A data model for 4D ramps from Liger or IRIS for the IFU or Imager. 4D arrays are formatted as (groups, reads, pixely, pixelx).

    Parameters:
    data (np.ndarray): 4-D array of counts for each read.
    dq (np.ndarray): 4-D data quality array for each read.
    """
    schema_url = "https://oirlab.github.io/schemas/RampModel.schema"

    def __init__(self, init=None, **kwargs):
        super().__init__(init=init, **kwargs)

        # Implicitly create arrays
        self.times = self.times
        self.data = self.data
        self.dq = self.dq