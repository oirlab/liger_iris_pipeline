from .model_base import LigerIRISDataModel

__all__ = ["ImagerModel"]


class ImagerModel(LigerIRISDataModel):
    """
    A data model for the typical data product from the Liger or IRIS imager (single detector).

    Parameters:
    data (np.ndarray): The science data array.
    err (np.ndarray): : The error array.
    dq (np.ndarray): 2D data quality array.
    """

    schema_url = "https://oirlab.github.io/schemas/LigerImagerModel.schema"

    def __init__(self, init=None, **kwargs):
        super().__init__(init=init, **kwargs)

        # Implicitly create arrays
        self.data = self.data
        self.err = self.err
        self.dq = self.dq