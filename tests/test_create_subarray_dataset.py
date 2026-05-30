# Imports
from liger_iris_pipeline.pipeline import Stage2ImagerPipeline
from liger_iris_pipeline import datamodels
import numpy as np

#from .utils import make_dark_model, make_detector_flat_model, make_science_imager_model


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

    shape = (4096, 4096)

    instrument_name = 'IRIS'

    science_model_L1 = datamodels.ImagerModel(
        data=np.ones(shape),
        meta={
            'instrument.name' : instrument_name,
            'data_level' : '1',
            'instrument.filter' : 'J'
        },
    )

    dark_model = datamodels.DarkModel(
        data=np.zeros(shape),
        meta={
            'instrument.name' : instrument_name,
            'instrument.filter' : 'J'
        },
    )

    gain_model = datamodels.GainModel(
        data=np.ones(shape),
        cov=np.zeros((2, 2, *shape)),
        meta={
            'instrument.name' : instrument_name,
            'instrument.filter' : 'J'
        },
    )

    flat_model = datamodels.DetectorFlatModel(
        data=np.ones(shape),
        meta={
            'instrument.name' : instrument_name,
            'instrument.filter' : 'J'
        },
    )

    # Setup the subarray params
    s1 = 300
    s2 = 100
    subarray_maps_metadata = []

    # Square subarray
    # Covers central bright star
    subarray_maps_metadata.append({
        "xstart" : 2048,
        "ystart" : 2048,
        "xsize" : s1,
        "ysize" : s1,
        "detxsize" : shape[1],
        "detysize" : shape[0],
        "fastaxis" : 0,
        "slowaxis" : 1,
    })

    # Rectangular subarray
    # Covers bottom left star
    subarray_maps_metadata.append({
        "xstart" : 100,
        "ystart" : 100,
        "xsize" : s2,
        "ysize" : s2 // 2,
        "detxsize" : shape[1],
        "detysize" : shape[0],
        "fastaxis" : 0,
        "slowaxis" : 1,
    })

    # Create the subarray images for each subarray model
    # based on a copy of the full frame model
    subarray_models = {}
    for i, p in enumerate(subarray_maps_metadata):
        subarray_models[i+1] = science_model_L1.copy()
        for ext in ("data", "dq", "err", "subarray_map"):
            subarray_models[i+1][ext] = slice_subarray_mask(science_model_L1[ext], p)

    # Set the correct metadata for each subarray model
    for i, p in enumerate(subarray_maps_metadata):
        subarray_models[i+1].meta.subarray.name = "CUSTOM"
        subarray_models[i+1].meta.subarray.id = i + 1
        for k, v in p.items():
            setattr(subarray_models[i+1].meta.subarray, k, v)

    # Add subarr map to the full frame model
    science_model_L1.subarray_map = np.zeros_like(science_model_L1.data)
    for i, p in enumerate(subarray_maps_metadata):
        set_subarray_mask(science_model_L1.subarray_map, p, id=i+1)

    # Set all subarray regions to nan in full frame
    science_model_L1.data[science_model_L1.subarray_map != 0] = np.nan

    # Write the full frame
    sci_L1_filename = science_model_L1.generate_filename()
    full_frame_filename_temp = str(tmp_path / sci_L1_filename)
    science_model_L1.save(full_frame_filename_temp)

    # Write the subarrays
    subarray_filenames_temp = {}
    for k, sub_model in subarray_models.items():
        subarray_filenames_temp[k] = str(tmp_path / sci_L1_filename.replace('-00.fits', f'-0{k}.fits'))
        sub_model.save(subarray_filenames_temp[k])

    # Create and run the pipeline on the full frame
    reduced_full_frame = Stage2ImagerPipeline.call(
        {
            "SCI": [
                full_frame_filename_temp
            ]
        },
        steps={
            'dark_sub': {
                'dark': dark_model
            },
            'gain_corr': {
                'gain': gain_model
            },
            'detflat': {
                'detflat': flat_model
            },
            'background_sub' : {
                'do_scale_calc' : False,
            },
        }
    )[0]
    
    # Set the subarray metadata id to 0 (full frame)
    reduced_full_frame.meta.subarray.id = 0

    # Call the pipeline on the subarrays
    reduced_subarrays = {}
    for k in subarray_filenames_temp:
        reduced_subarrays[k] = Stage2ImagerPipeline.call(
            {
                "SCI": [
                    subarray_filenames_temp[k]
                ]
            },
            steps={
                'dark_sub': {
                    'dark': dark_model
                },
                'gain_corr': {
                    'gain': gain_model
                },
                'detflat': {
                    'detflat': flat_model
                },
                'background_sub' : {
                    'do_scale_calc' : False,
                },
            }
        )[0]

    # Check the metadata on the reduced full frame model and each reduced subarray model
    for k, full_frame_meta, each_input in zip(
            range(1, len(subarray_maps_metadata) + 1),
            reduced_full_frame.meta.subarray_map,
            subarray_maps_metadata,
        ):
        assert reduced_subarrays[k].meta.subarray.instance == dict(name="CUSTOM", id=k, **each_input)