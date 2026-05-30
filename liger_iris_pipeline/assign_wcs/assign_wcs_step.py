from ..stpipe.base_step import LigerIRISStep
from .. import datamodels
from ..datamodels import ImagerModel, LigerIRISDataModel

import logging

from .assign_wcs_utils import load_wcs_imager

logger = logging.getLogger(__name__)

__all__ = ["AssignWCSStep"]


class AssignWCSStep(LigerIRISStep):
    """
    Associates a world coordinate system (WCS) object with a science exposure.

    Currently the Liger IRIS DRS implements a very simple model that expects standard FITS WCS keywords in the header and uses `astropy.modeling <https://docs.astropy.org/en/stable/modeling/index.html>`_ to build a transformation pipeline, wrap it into a generalized WCS ``gwcs.WCS`` object and store it as ``output_model.meta.wcs``, as it is expected by Stage 3 pipelines.

    The forward direction of the transforms is from detector to world coordinates and the input positions are 0-based.

    This step expects to find the basic WCS keywords in the PRIMARY extension header. Distortion WCS models are not implemented yet and will be stored in reference files in the `ASDF <http://asdf-standard.readthedocs.org/en/latest/>`_ format in future versions.

    Parameters
    ----------
    input : ImagerModel or IFSCubeModel
        Data model to which WCS will be assigned.

    Calibrations
    ------------

    WCS reference files will be saved in ASDF format. The best way to create the file is to programmatically create the model and then save it to a file. A tutorial on creating reference files in ASDF format is available at:

    https://github.com/spacetelescope/jwreftools/blob/master/docs/notebooks/referece_files_asdf.ipynb

    **One must install the package ``asdf-astropy`` to serialize astropy models into ASDF format.**
    
    Returns
    -------
    output
        Data model with WCS assigned (same type as input).
    """

    class_alias = "assign_wcs"

    def process(self, input):
        reference_file_names = {}
        input_model = self.open_model(input)
        output_model = load_wcs_imager(input_model, reference_file_names)
        return output_model
