# Imports
import liger_iris_pipeline
from liger_iris_pipeline import datamodels
import numpy as np
from liger_iris_pipeline.tests.utils import download_osf_file


def create_subarray_model(name, xstart, ystart, xsize, ysize):
    # Download the science frame and open
    sci_L1_filepath = download_osf_file('Liger/L1/2024B-P001-001_Liger_IMG_SCI_LVL1_0001_M13-J-10mas.fits', use_cached=True)
    input_model = datamodels.ImagerModel(sci_L1_filepath)

    # Setup the subarray params
    input_model.meta.subarray.name = name
    input_model.meta.subarray.xstart = xstart
    input_model.meta.subarray.ystart = ystart
    input_model.meta.subarray.xsize = xsize
    input_model.meta.subarray.ysize = ysize
    input_model.meta.subarray.detxsize = 2048
    input_model.meta.subarray.detysize = 2048
    input_model.meta.subarray.fastaxis = 0
    input_model.meta.subarray.slowaxis = 1

    return input_model


def test_dark_subarray():

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
    input_model.err = input_model.err[subarray_slice]
    input_model.dq = input_model.dq[subarray_slice]

    # Ensure correct subarray shape
    assert input_model.data.shape == (ysize, xsize)

    # Setup the Dark step
    step = liger_iris_pipeline.DarkSubtractionStep()

    # Run on the subarray
    dark_filepath = download_osf_file('Liger/Cals/Liger_IMG_DARK_20240924000000_0.0.1.fits', use_cached=True)
    step_output = step.run(input_model, dark=dark_filepath)

    # Test the output shape
    assert step_output.data.shape == (ysize, xsize)

    # Open the dark cal that was used
    dark_model = datamodels.DarkModel(step.dark_filepath)

    # Compare the output with a manual dark subtraction
    np.testing.assert_allclose(
        step_output.data,
        input_model.data - dark_model.data[ystart-1:ystart-1+ysize, xstart-1:xstart-1+xsize]
    )