from .referencefile import ReferenceFileModel

__all__ = ['FlatModel']


class FlatModel(ReferenceFileModel):
    """
    A data model for flat field images from either the Liger or IRIS Imager or IFU.
    """
    schema_url = "https://oirlab.github.io/schemas/LigerFlatModel.schema"