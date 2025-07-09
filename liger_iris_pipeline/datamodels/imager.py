from .model_base import LigerIRISDataModel

__all__ = ["ImagerModel"]

class ImagerModel(LigerIRISDataModel):
    """
    A data model for the typical data product from the Liger or IRIS imager (single detector).
    """
    schema_url = "https://oirlab.github.io/schemas/ImagerModel.schema"