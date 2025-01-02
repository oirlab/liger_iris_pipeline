# Imports
import liger_iris_pipeline
import numpy as np
import os


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

def create_config():
    conf = """
    name = "ImagerStage2Pipeline"
    class = "liger_iris_pipeline.pipeline.ImagerStage2Pipeline"
    save_results = True

    [steps]
        [[dark_sub]]
        [[flat_field]]
        [[sky_sub]]
        [[assign_wcs]]
            skip = True
        [[photom]]
            skip = True
        [[resample]]
            skip = True
    """
    return conf

def test_create_subarray_dataset(tmp_path):

    # Download the science frame and open
    sci_L1_filename = "/Users/cale/Desktop/Liger_IRIS_Test_Data/IRIS/2024A-P123-044_IRIS_IMG1_SCI-J1458+1013-SIM-Y_LVL1_0001-00.fits"
    input_model = liger_iris_pipeline.ImagerModel(sci_L1_filename)

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
    #full_frame_filename_temp = tmp_path / os.path.basename(sci_L1_filename.replace('-00.fits', '-01.fits'))
    full_frame_filename_temp = tmp_path / os.path.basename(sci_L1_filename)
    input_model.write(full_frame_filename_temp)

    # Write the subarrays
    subarray_filenames_temp = {}
    for k, sub_model in subarray_models.items():
        subarray_filenames_temp[k] = tmp_path / os.path.basename(sci_L1_filename.replace('-00.fits', f'-0{k}.fits'))
        sub_model.write(subarray_filenames_temp[k])

    # Create the config file
    conf = create_config()
    config_file = tmp_path / "test_config.cfg"
    with open(config_file, "w") as f:
        f.write(conf)

    # Create and run the pipeline on the full frame
    #pipeline = liger_iris_pipeline.ImagerStage2Pipeline()
    results = liger_iris_pipeline.ImagerStage2Pipeline.call(full_frame_filename_temp, config_file=config_file)
    reduced_full_frame = results[0]

    # Set the subarray metadata id to 0 (full frame)
    reduced_full_frame.meta.subarray.id = 0

    # Write the reduced full frame
    reduced_full_frame.write(str(full_frame_filename_temp).replace('_LVL1', '_LVL2'))

    # Call the pipeline on the subarrays
    reduced_subarrays = {}
    for k in subarray_filenames_temp:
        reduced_subarrays[k] = liger_iris_pipeline.ImagerStage2Pipeline.call(subarray_filenames_temp[k], config_file=config_file)[0]
        reduced_subarrays[k].save(str(subarray_filenames_temp[k]).replace(('_LVL1', '-_LVL2')))

    # Check the metadata on the reduced full frame model and each reduced subarray model
    for k, full_frame_meta, each_input in zip(
            range(1, len(subarray_maps_metadata)+1),
            reduced_full_frame.meta.subarray_map,
            subarray_maps_metadata,
        ):
        assert full_frame_meta.instance == each_input
        assert reduced_subarrays[k].meta.subarray.instance == dict(name="CUSTOM", id=k, **each_input)

