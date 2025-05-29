from .referencefile import ReferenceFileModel

__all__ = ['BiasModel']


class BiasModel(ReferenceFileModel):
    """
    A bias model for bias levels from either the Liger or IRIS Imager or IFU.
    """
    schema_url = "https://oirlab.github.io/schemas/BiasModel.schema"
    _ref_type = "bias"