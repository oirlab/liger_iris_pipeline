from liger_iris_pipeline import DarkSubtractionStep
import numpy as np
from .utils import make_science_imager_model, make_dark_model

def create_subarray_model(name, xstart, ystart, xsize, ysize):
    science_model = make_science_imager_model(instrument_name='IRIS')
    science_model.meta.subarray.name = name
    science_model.meta.subarray.xstart = xstart
    science_model.meta.subarray.ystart = ystart
    science_model.meta.subarray.xsize = xsize
    science_model.meta.subarray.ysize = ysize
    science_model.meta.subarray.detxsize = science_model.shape[1]
    science_model.meta.subarray.detysize = science_model.shape[0]
    science_model.meta.subarray.fastaxis = 0
    science_model.meta.subarray.slowaxis = 1
    return science_model

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

    # Run on the subarray
    dark_model = make_dark_model(instrument_name='IRIS', meta={'instrument.mode': 'IMG'})
    output_model = DarkSubtractionStep.call(input_model.copy(), dark=dark_model)

    # Test the output shape
    assert output_model.data.shape == (ysize, xsize)

    # Compare the output with a manual dark subtraction
    np.testing.assert_allclose(
        output_model.data,
        input_model.data - dark_model.data[ystart-1:ystart-1+ysize, xstart-1:xstart-1+xsize]
    )