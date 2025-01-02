
import numpy as np
import liger_iris_pipeline
from liger_iris_pipeline import datamodels

def test_dark_step():
    sci_L1_filename = "/Users/cale/Desktop/Liger_IRIS_Test_Data/IRIS/2024A-P123-044_IRIS_IMG1_SCI-J1458+1013-SIM-Y_LVL1_0001-00.fits"
    input_model = datamodels.open(sci_L1_filename)

    step = liger_iris_pipeline.DarkSubtractionStep()
    step_output = step.run(sci_L1_filename)
    dark_model = datamodels.open(step.dark_filename)

    np.testing.assert_allclose(step_output.data, input_model.data - dark_model.data)