from .referencefile import ReferenceFileModel

__all__ = ['NonlinearReadoutParametersModel']


class NonlinearReadoutParametersModel(ReferenceFileModel):
    """
    A data model for the detector nonlinear readout polynomial coeffs.
    """
    schema_url = "https://oirlab.github.io/schemas/NonlinearReadoutParametersModel.schema"
    _ref_type = "nonlin"