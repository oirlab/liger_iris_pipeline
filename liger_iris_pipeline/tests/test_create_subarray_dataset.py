# Imports
import liger_iris_pipeline
from liger_iris_pipeline import datamodels
import numpy as np
import os
from liger_iris_pipeline.utils.gdrive import download_gdrive_file


# Converts 1->0 indexing, sets the subarray index
def set_subarray_mask(mask_array, subarray_params, id):
    xstart, ystart = subarray_params['xstart'], subarray_params['ystart']
    xsize, ysize = subarray_params['xsize'], subarray_params['ysize']
    xstart = xstart - 1
    ystart = ystart - 1
    mask_array[ystart:ystart+ysize, xstart:xstart+xsize] = id


# Converts 1->0 indexing, slices the subarray, and returns a copy
def slice_subarray_mask(mask_array, subarray_params):
    xstart, ystart = subarray_params['xstart'], subarray_params['ystart']
    xsize, ysize = subarray_params['xsize'], subarray_params['ysize']
    xstart = xstart - 1
    ystart = ystart - 1
    return mask_array[ystart:ystart+ysize, xstart:xstart+xsize].copy()


def test_create_subarray_dataset(tmp_path):

    # Download the science frame and open
    sci_L1_filepath = download_gdrive_file('Liger/L1/2024B-P001-001_Liger_IMG_SCI_LVL1_0001_M13-J-10mas-skyscale1.0.fits', use_cached=True)
    dark_filepath = download_gdrive_file('Liger/Cals/Liger_IMG_DARK_20240924000000_0.0.1.fits', use_cached=True)
    flat_filepath = download_gdrive_file('Liger/Cals/Liger_IMG_FLAT_20240924000000_0.0.1.fits', use_cached=True)
    input_model = datamodels.ImagerModel(sci_L1_filepath)

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
        "ysize" : s1,
        "detxsize" : 2048,
        "detysize" : 2048,
        "fastaxis" : 0,
        "slowaxis" : 1,
    })

    # Rectangular subarray
    # Covers bottom left star
    subarray_maps_metadata.append({
        "xstart" : 1040 - s2 // 2,
        "ystart" : 1040 - s2 // 2,
        "xsize" : s2,
        "ysize" : s2 // 2,
        "detxsize" : 2048,
        "detysize" : 2048,
        "fastaxis" : 0,
        "slowaxis" : 1,
    })

    # Create the subarray images for each subarray model
    # based on a copy of the full frame model
    subarray_models = {}
    for i, p in enumerate(subarray_maps_metadata):
        subarray_models[i+1] = input_model.copy()
        for ext in ("data", "dq", "err"):
            subarray_models[i+1][ext] = slice_subarray_mask(input_model[ext], p)

    # Set the correct metadata for each subarray model
    for i, p in enumerate(subarray_maps_metadata):
        subarray_models[i+1].meta.subarray.name = "CUSTOM"
        subarray_models[i+1].meta.subarray.id = i + 1
        for k, v in p.items():
            setattr(subarray_models[i+1].meta.subarray, k, v)

    # Add subarr map to the full frame model
    input_model.subarr_map = np.zeros_like(input_model.data)
    for i, p in enumerate(subarray_maps_metadata):
        set_subarray_mask(input_model.subarr_map, p, id=i+1)

    # Set all subarray regions to nan in full frame
    input_model.data[input_model.subarr_map != 0] = np.nan

    # Write the full frame
    full_frame_filename_temp = str(tmp_path / os.path.basename(sci_L1_filepath))
    input_model.save(full_frame_filename_temp)

    # Write the subarrays
    subarray_filenames_temp = {}
    for k, sub_model in subarray_models.items():
        subarray_filenames_temp[k] = str(tmp_path / os.path.basename(sci_L1_filepath.replace('-00.fits', f'-0{k}.fits')))
        sub_model.save(subarray_filenames_temp[k])

    # Create and run the pipeline on the full frame
    pipeline = liger_iris_pipeline.ImagerStage2Pipeline()
    pipeline.dark_sub.dark = dark_filepath
    pipeline.flat_field.flat = flat_filepath
    reduced_full_frame = pipeline.run({"SCI": [full_frame_filename_temp]}, output_dir=str(tmp_path))[0]

    # Set the subarray metadata id to 0 (full frame)
    reduced_full_frame.meta.subarray.id = 0

    # Call the pipeline on the subarrays
    reduced_subarrays = {}
    for k in subarray_filenames_temp:
        pipeline = liger_iris_pipeline.ImagerStage2Pipeline()
        pipeline.dark_sub.dark = dark_filepath
        pipeline.flat_field.flat = flat_filepath
        reduced_subarrays[k] = pipeline.run({"SCI": [subarray_filenames_temp[k]]}, output_dir=str(tmp_path))[0]

    # Check the metadata on the reduced full frame model and each reduced subarray model
    for k, full_frame_meta, each_input in zip(
            range(1, len(subarray_maps_metadata)+1),
            reduced_full_frame.meta.subarray_map,
            subarray_maps_metadata,
        ):
        assert reduced_subarrays[k].meta.subarray.instance == dict(name="CUSTOM", id=k, **each_input)