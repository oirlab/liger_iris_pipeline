# Imports
import liger_iris_pipeline
from liger_iris_pipeline import datamodels
import numpy as np
from liger_iris_pipeline.tests.utils import download_osf_file


def create_subarray_model(name, xstart, ystart, xsize, ysize):

    # Download the science frame and open
    remote_sci_L1_filename = 'IRIS/L1/2024B-P123-008_IRIS_IMG1_SCI-J1458+1013-Y-4.0_LVL1_0001-00.fits'
    sci_L1_filename = download_osf_file(remote_sci_L1_filename, use_cached=True)
    input_model = datamodels.ImagerModel(sci_L1_filename)

    # Setup the subarray params
    input_model.meta.subarray.name = name
    input_model.meta.subarray.xstart = xstart
    input_model.meta.subarray.ystart = ystart
    input_model.meta.subarray.xsize = xsize
    input_model.meta.subarray.ysize = ysize
    input_model.meta.subarray.detxsiz = 4096
    input_model.meta.subarray.detysiz = 4096
    input_model.meta.subarray.fastaxis = 0
    input_model.meta.subarray.slowaxis = 1

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
    step = liger_iris_pipeline.DarkSubtractionStep()

    # Run on the subarray
    step_output = step.run(input_model)

    # Test the output shape
    assert step_output.data.shape == (ysize, xsize)

    # Open the dark cal that was used
    dark_model = datamodels.ImagerModel(step.dark_filename)

    # Compare the output with a manual dark subtraction
    np.testing.assert_allclose(
        step_output.data,
        input_model.data - dark_model.data[ystart-1:ystart-1+ysize, xstart-1:xstart-1+xsize]
    )