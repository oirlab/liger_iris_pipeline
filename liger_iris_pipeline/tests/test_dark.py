
import numpy as np
import liger_iris_pipeline
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.tests.utils import download_osf_file

def test_dark_step():

    remote_sci_L1_filename = 'IRIS/L1/2024B-P123-008_IRIS_IMG1_SCI-J1458+1013-Y-4.0_LVL1_0001-00.fits'
    sci_L1_filename = download_osf_file(remote_sci_L1_filename, use_cached=True)
    input_model = datamodels.open(sci_L1_filename)

    step = liger_iris_pipeline.DarkSubtractionStep()
    step_output = step.run(sci_L1_filename)
    dark_model = datamodels.open(step.dark_filename)

    np.testing.assert_allclose(step_output.data, input_model.data - dark_model.data)