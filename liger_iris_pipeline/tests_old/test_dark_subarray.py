# Imports
import liger_iris_pipeline
liger_iris_pipeline.monkeypatch_jwst_datamodels()
import numpy as np

# See README.md for notes on testing data
from liger_iris_pipeline.tests.test_utils import get_data_from_url


def test_dark_subarray(tmp_path):

    # Download the science frame and open
    raw_science_filename = get_data_from_url("48191524")
    input_model = liger_iris_pipeline.datamodels.LigerIrisImageModel(raw_science_filename)

    # Setup the subarray params
    xstart = 100
    ystart = 200
    xsize = 50
    ysize = 60
    input_model.meta.subarray.name = "CUSTOM"
    input_model.meta.subarray.xstart = xstart
    input_model.meta.subarray.ystart = ystart
    input_model.meta.subarray.xsize = xsize
    input_model.meta.subarray.ysize = ysize

    # Slice the data
    subarray_slice = np.s_[ystart:ystart+ysize, xstart:xstart+xsize]
    input_model.data = input_model.data[subarray_slice]
    input_model.dq = input_model.dq[subarray_slice]

    # Ensure correct subarray shape
    assert input_model.data.shape == (ysize, xsize)

    # Setup the Dark step
    step = liger_iris_pipeline.dark_current.DarkCurrentStep()

    # Run on the subarray
    step_output = step.run(input_model)

    # Test the output shape
    assert step_output.data.shape == (ysize, xsize)

    # Open the dark cal that was used
    dark_model = liger_iris_pipeline.datamodels.LigerIrisImageModel(step.dark_name)

    # Compare the output with a manual dark subtraction
    np.testing.assert_allclose(
        step_output.data,
        input_model.data - dark_model.data[ystart-1:ystart-1+ysize, xstart-1:xstart-1+xsize]
    )