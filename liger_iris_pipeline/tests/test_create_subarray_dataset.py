# Imports
import liger_iris_pipeline
import numpy as np

# See README.md for notes on testing data
from liger_iris_pipeline.tests.test_utils import get_data_from_url


# Converts 1->0 indexing, sets the subarray index
def set_subarray_mask(mask_array, subarray_index, xstart, ystart, xsize, ysize):
    xstart = xstart - 1
    ystart = ystart - 1
    mask_array[ystart:ystart+ysize, xstart:xstart+xsize] = subarray_index


# Converts 1->0 indexing, slices the subarray, and returns a copy
def slice_subarray_mask(mask_array, xstart, ystart, xsize, ysize):
    xstart = xstart - 1
    ystart = ystart - 1
    return mask_array[ystart:ystart+ysize, xstart:xstart+xsize].copy()


def test_create_subarray_dataset(tmp_path):

    # Download the science frame and open
    #raw_science_filename = get_data_from_url("48191524")
    raw_science_filename = "/Users/cale/Desktop/IRIS_Test_Data/raw_frame_sci_20240805.fits"
    input_model = liger_iris_pipeline.ImagerModel(raw_science_filename)

    # Setup the subarray params
    s1 = 300
    s2 = 100
    subarray_maps_metadata = []

    # Square subarray
    # Covers central bright star
    subarray_maps_metadata.append({
        "xstart" : 2048 - s1 // 2,
        "ystart" : 2048 - s1 // 2,
        "xsize" : s1,
        "ysize" : s1
    })

    # Rectangular subarray
    # Covers bottom left star
    subarray_maps_metadata.append({
        "xstart" : 1040 - s2 // 2,
        "ystart" : 1040 - s2 // 2,
        "xsize" : s2,
        "ysize" : s2 // 2
    })

    # Create the subarray images for each subarray model
    # based on a copy of the full frame model
    subarray_models = {}
    for i, shape in enumerate(subarray_maps_metadata):
        subarray_models[i+1] = input_model.copy()
        for ext in ("data", "dq", "err"):
            subarray_models[i+1][ext] = slice_subarray_mask(input_model[ext], **shape)

    # Set the correct metadata for each subarray model
    for i, shape in enumerate(subarray_maps_metadata):
        subarray_models[i+1].meta.subarray.name = "CUSTOM"
        subarray_models[i+1].meta.subarray.id = i + 1
        for k, v in shape.items():
            setattr(subarray_models[i+1].meta.subarray, k, v)

    # Add subarr map to the full frame model
    input_model.subarr_map = np.zeros_like(input_model.data)
    for i, shape in enumerate(subarray_maps_metadata):
        set_subarray_mask(input_model.subarr_map, subarray_index=i+1, **shape)

    # Set all subarray regions to nan in full frame
    input_model.data[input_model.subarr_map != 0] = np.nan

    # Write the full frame
    full_frame_filename_temp = tmp_path / "raw_science_frame_sci_with_subarrays.fits"
    input_model.write(full_frame_filename_temp)

    # Write the subarrays
    subarray_filenames_temp = {}
    for k, sub_model in subarray_models.items():
        subarray_filenames_temp[k] = tmp_path / f"raw_science_frame_sci_subarray_{k}.fits"
        sub_model.write(subarray_filenames_temp[k])

    # Create and run the pipeline on the full frame
    pipeline = liger_iris_pipeline.ImagerStage2Pipeline()
    reduced_full_frame = pipeline.call(full_frame_filename_temp, config_file="liger_iris_pipeline/tests/data/image2_iris.cfg")[0]

    # Set the subarray metadata id to 0 (full frame)
    reduced_full_frame.meta.subarray.id = 0

    # Write the reduced full frame
    reduced_full_frame.write(str(full_frame_filename_temp).replace("raw", "reduced"))

    # Call the pipeline on the subarrays
    reduced_subarrays = {}
    for k in subarray_filenames_temp:
        reduced_subarrays[k] = pipeline.call(subarray_filenames_temp[k], config_file="liger_iris_pipeline/tests/data/image2_iris.cfg")[0]
        reduced_subarrays[k].write(str(subarray_filenames_temp[k]).replace("raw", "reduced"))

    # Check the metadata on the reduced full frame model and each reduced subarray model
    for k, full_frame_meta, each_input in zip(
            range(1, len(subarray_maps_metadata)+1),
            reduced_full_frame.meta.subarray_map,
            subarray_maps_metadata,
        ):
        assert full_frame_meta.instance == each_input
        assert reduced_subarrays[k].meta.subarray.instance == dict(name="CUSTOM", id=k, **each_input)

