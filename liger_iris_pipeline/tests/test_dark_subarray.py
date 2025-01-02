# Imports
import liger_iris_pipeline
import numpy as np

# See README.md for notes on testing data
from liger_iris_pipeline.tests.test_utils import get_data_from_url



def create_subarray_model(name, xstart, ystart, xsize, ysize):

    # Download the science frame and open
    sci_L1_filename = "/Users/cale/Desktop/Liger_IRIS_Test_Data/IRIS/2024A-P123-044_IRIS_IMG1_SCI-J1458+1013-SIM-Y_LVL1_0001.fits"
    input_model = liger_iris_pipeline.ImagerModel(sci_L1_filename)

    # Setup the subarray params
    input_model.meta.subarray.name = name
    input_model.meta.subarray.xstart = xstart
    input_model.meta.subarray.ystart = ystart
    input_model.meta.subarray.xsize = xsize
    input_model.meta.subarray.ysize = ysize

    return input_model


def test_dark_subarray(tmp_path):

    # Get model
    name = "CUSTOM"
    xstart = 100
    ystart = 200
    xsize = 50
    ysize = 60
    input_model = create_subarray_model(name, xstart, ystart, xsize, ysize)

    # Slice the data
    subarray_slice = np.s_[ystart:ystart+ysize, xstart:xstart+xsize]
    input_model.data = input_model.data[subarray_slice]
    input_model.dq = input_model.dq[subarray_slice]

    # Ensure correct subarray shape
    assert input_model.data.shape == (ysize, xsize)

    # Setup the Dark step
    step = liger_iris_pipeline.DarkCurrentStep()

    # Run on the subarray
    step_output = step.run(input_model)

    # Test the output shape
    assert step_output.data.shape == (ysize, xsize)

    # Open the dark cal that was used
    dark_model = liger_iris_pipeline.ImagerModel(step.dark_name)

    # Compare the output with a manual dark subtraction
    np.testing.assert_allclose(
        step_output.data,
        input_model.data - dark_model.data[ystart-1:ystart-1+ysize, xstart-1:xstart-1+xsize]
    )