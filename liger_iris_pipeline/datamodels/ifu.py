from .model_base import LigerIRISDataModel


__all__ = ['IFUImageModel', 'IFUCubeModel']


class IFUImageModel(LigerIRISDataModel):
    """
    A data model for IFU data at the 2D image stage.
    """

    schema_url = "https://oirlab.github.io/schemas/IFUImageModel.schema"

    #def __init__(self, init=None, **kwargs):

        # super().__init__(init=init, **kwargs)
        # self.data = self.data
        # self.err = self.err
        # self.dq = self.dq


class IFUCubeModel(LigerIRISDataModel):
    """
    A data model for IFU data at the 3D cube stage.
    """

    schema_url = "https://oirlab.github.io/schemas/IFUCubeModel.schema"

    #def __init__(self, init=None, **kwargs):

        # super().__init__(init=init, **kwargs)

        # # Implicitly create arrays
        # self.wavelength = self.wavelength
        # self.data = self.data
        # self.err = self.err
        # self.dq = self.dq