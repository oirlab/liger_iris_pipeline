
import numpy as np
from liger_iris_pipeline import datamodels, FlatFieldStep


def test_flat_step():
    sci_L1_filename = "/Users/cale/Desktop/Liger_IRIS_Test_Data/IRIS/2024A-P123-044_IRIS_IMG1_SCI-J1458+1013-SIM-Y_LVL1_0001-00.fits"
    input_model = datamodels.open(sci_L1_filename)

    step = FlatFieldStep()
    step_output = step.run(sci_L1_filename)
    flat_model = datamodels.open(step.flat_filename)

    np.testing.assert_allclose(step_output.data, input_model.data / flat_model.data)