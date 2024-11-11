from stdatamodels.dynamicdq import dynamic_mask
from .dqflags import pixel
from .reference import ReferenceFileModel


__all__ = ['FlatModel']


class FlatModel(ReferenceFileModel):
    """
    A data model for 2D flat-field images.

    Parameters
    __________
    data : numpy float32 array
         The science data

    dq : numpy uint32 array
         Data quality array

    err : numpy float32 array
         Error array

    dq_def : numpy table
         DQ flag definitions
    """
    #schema_url = "https://oirlab.github.io/liger-iris-pipeline/schemas/liger_iris_datamodel/flat.schema"
    schema_url = "https://oirlab.github.io/schemas/flat.schema"

    def __init__(self, init=None, **kwargs):
        super(FlatModel, self).__init__(init=init, **kwargs)

        self.dq = dynamic_mask(self, pixel)

        # Implicitly create arrays
        self.err = self.err
