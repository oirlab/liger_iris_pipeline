# Imports
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.datamodels.dqflags import DQ_FLAGS
from liger_iris_pipeline.subarrays.parse_subarray_map_step import parse_subarray_map, ParseSubarrayMapStep
import numpy as np

def set_subarray_mask(mask_array, p):
    xstart = p["xstart"]
    ystart = p["ystart"]
    xsize = p["xsize"]
    ysize = p["ysize"]
    xstart = xstart - 1
    ystart = ystart - 1
    mask_array[ystart:ystart + ysize, xstart:xstart + xsize] =  p['id']

def test_parse_subarray_map():

    shape = (100, 100)

    # Define simple subarray metadata and image ID map
    # ID is just the 1-based index in this list (1, 2, ...)
    subarray_maps_metadata = [
        {
            "xstart" : 80, "ystart" : 70,
            "xsize" : 10, "ysize" : 10,
            "id" : 1,
            "detxsize" : shape[1], "detysize" : shape[0],
            "fastaxis" : 0, "slowaxis" : 1
        },
        {
            "xstart" : 10, "ystart" : 20,
            "xsize" : 20, "ysize" : 20,
            "id" : 2,
            "detxsize" : shape[1], "detysize" : shape[0],
            "fastaxis" : 0, "slowaxis" : 1
        },
    ]
    subarray_map = np.zeros(shape, dtype=np.uint8)
    for p in subarray_maps_metadata:
        set_subarray_mask(subarray_map, p)
    
    # Test parse_subarray_map function
    parse_subarray_map_output = parse_subarray_map(subarray_map)
    assert subarray_maps_metadata == parse_subarray_map_output

    # Create toy Image object with these subarrays
    model = datamodels.ImagerModel(data=np.zeros(shape), instrument_name='Liger')
    model.dq[25, 25] = 1
    model.dq[26, 26] = 1
    model.subarray_map = subarray_map

    # Test the step class
    step = ParseSubarrayMapStep()
    output_model = step.run(model)

    # Test each parsed subarray map is equal to what we defined above.
    for each_parsed, each_input in zip(output_model.meta.subarray_map, subarray_maps_metadata):
        assert each_parsed.instance == each_input

    # Check bad pixel is still maintained
    assert output_model.dq[25, 25] == DQ_FLAGS['SUBARRAY'] + 1

    # Test DQ flags
    np.testing.assert_array_equal(
        np.bitwise_and(output_model.dq, DQ_FLAGS['SUBARRAY']) > 0,
        subarray_map != 0
    )