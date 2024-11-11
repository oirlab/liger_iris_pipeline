from .referencefile import ReferenceFileModel

__all__ = ['DarkModel']


class DarkModel(ReferenceFileModel):
    """
    A data model for darks from either the Liger or IRIS Imager or IFU.
    """
    schema_url = "https://oirlab.github.io/schemas/dark.schema"