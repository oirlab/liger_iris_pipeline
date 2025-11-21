from .referencefile import ReferenceFileModel

__all__ = ['DistortionMapModel']


class DistortionMapModel(ReferenceFileModel):
    """
    A data model for distortion map reference files.
    """
    schema_url = "https://oirlab.github.io/schemas/DistortionMapModel.schema"
    _ref_type = "distortion_map"