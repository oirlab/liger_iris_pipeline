from .referencefile import ReferenceFileModel

__all__ = ['NonlinearCorrectionModel']


class NonlinearCorrectionModel(ReferenceFileModel):
    """
    A data model for the detector nonlinear readout polynomial coeffs.
    """
    schema_url = "https://oirlab.github.io/schemas/NonlinearCorrectionModel.schema"
    _ref_type = "nonlin"