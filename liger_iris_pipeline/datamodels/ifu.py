from .model_base import LigerIRISDataModel


__all__ = ['IFUImageModel', 'IFUCubeModel']


class IFUImageModel(LigerIRISDataModel):
    """
    A data model for IFU data at the 2D image stage.
    
    Parameters:
    data (np.ndarray): The science data.
    err (np.ndarray): : The error array.
    dq (np.ndarray): The 2D data quality array.
    """

    schema_url = "https://oirlab.github.io/schemas/IFUImageModel.schema"

    def __init__(self, init=None, **kwargs):

        super().__init__(init=init, **kwargs)

        # Implicitly create arrays
        self.data = self.data
        self.err = self.err
        self.dq = self.dq


class IFUCubeModel(LigerIRISDataModel):
    """
    A data model for IFU data at the 3D cube stage.
    
    Parameters:
    wavelength (np.ndarray): The wavelength vector.
    data (np.ndarray): The science data cube.
    err (np.ndarray): : The error array cube.
    dq (np.ndarray): The 3D data quality array cube.
    """

    schema_url = "https://oirlab.github.io/schemas/IFUCubeModel.schema"

    def __init__(self, init=None, **kwargs):

        super().__init__(init=init, **kwargs)

        # Implicitly create arrays
        self.wavelength = self.wavelength
        self.data = self.data
        self.err = self.err
        self.dq = self.dq