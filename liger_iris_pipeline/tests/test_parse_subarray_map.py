# Imports
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.parse_subarray_map.parse_subarray_map_step import parse_subarray_map
from liger_iris_pipeline import ParseSubarrayMapStep
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

    # Define simple subarray metadata and image ID map
    # ID is just the 1-based index in this list (1, 2, ...)
    subarray_maps_metadata = [
        {"xstart" : 80, "ystart" : 70, "xsize" : 10, "ysize" : 10, "id" : 1, "detxsize" : 100, "detysize" : 100, "fastaxis" : 0, "slowaxis" : 1},
        {"xstart" : 10, "ystart" : 20, "xsize" : 20, "ysize" : 20, "id" : 2, "detxsize" : 100, "detysize" : 100, "fastaxis" : 0, "slowaxis" : 1},
    ]
    subarr_map = np.zeros((100, 100), dtype=np.int8)
    for p in subarray_maps_metadata:
        set_subarray_mask(subarr_map, p)
    
    # Test parse_subarray_map function
    parse_subarray_map_output = parse_subarray_map(subarr_map)
    assert subarray_maps_metadata == parse_subarray_map_output

    # Create toy Image object with these subarrays
    image = datamodels.ImagerModel(data=np.zeros((100, 100)))
    image.dq[25, 25] = 16
    image.dq[26, 26] = 1
    image["subarr_map"] = subarr_map

    # Test the step class
    step = ParseSubarrayMapStep()
    output = step.run(image)

    # Test each parsed subarray map is equal to what we defined above.
    for each_parsed, each_input in zip(output.meta.subarray, subarray_maps_metadata):
        assert each_parsed.instance == each_input

    # If a pixel is already flagged as subarray, don't mess it up
    assert output.dq[25, 25] == 16

    # conserve existing flags
    assert output.dq[26, 26] == 17

    # Test DQ flags
    np.testing.assert_array_equal(
        np.bitwise_and(output.dq, int(2**4)) > 0,
        subarr_map != 0
    )