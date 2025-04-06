# Imports
import liger_iris_pipeline
import liger_iris_pipeline.datamodels as datamodels
import numpy as np
import os
from liger_iris_pipeline.tests.utils import download_osf_file

def test_imager_stage2(tmp_path):

    # Create a temporary config file
    conf = """
    class = "liger_iris_pipeline.ImagerStage2Pipeline"
    save_results = True

    [steps]
        [[dark_sub]]
            config_file = "dark_config.cfg"
            save_results = True
        [[flat_field]]
        [[sky_sub]]
        [[assign_wcs]]
            skip = False
    """
    config_file = str(tmp_path / "test_config.cfg")
    with open(config_file, "w") as f:
        f.write(conf)

    # Create a temporary dark config file
    conf = """
    class = "liger_iris_pipeline.DarkSubtraction"
    """
    config_file_dark = str(tmp_path / "dark_config.cfg")
    with open(config_file_dark, "w") as f:
        f.write(conf)

    # Files
    remote_sci_L1_filename = 'IRIS/L1/2024B-P123-008_IRIS_IMG1_SCI-J1458+1013-Y-4.0_LVL1_0001-00.fits'
    remote_sky_L1_filename = 'IRIS/L1/2024B-P123-008_IRIS_IMG1_SKY-J1458+1013-Y-4.0_LVL1_0001-00.fits'
    sci_L1_filename = download_osf_file(remote_sci_L1_filename, use_cached=True)
    sky_bkg_L1_filename = download_osf_file(remote_sky_L1_filename, use_cached=True)

    # Setup input
    input = {
        "SCI": sci_L1_filename,
        "SKY": sky_bkg_L1_filename,
    }

    # Create and call the pipeline object
    pipeline = liger_iris_pipeline.ImagerStage2Pipeline(config_file=config_file)
    model_result = pipeline.run(input, output_dir=str(tmp_path))

    # Manual L2 file
    with datamodels.open(pipeline.dark_sub.dark_filename) as dark_model, \
        datamodels.open(pipeline.flat_field.flat_filename) as flat_model, \
        datamodels.open(sci_L1_filename) as sci_model, \
        datamodels.open(sky_bkg_L1_filename) as bkg_model:
        ref_data = (sci_model.data - dark_model.data) / flat_model.data - bkg_model.data
        np.testing.assert_allclose(model_result.data, ref_data, rtol=1e-6)


def test_imager_stage2_subarray(tmp_path):

    # Create a temporary config file
    conf = """
    class = "liger_iris_pipeline.ImagerStage2Pipeline"
    save_results = True

    [steps]
        [[dark_sub]]
            config_file = "dark_config.cfg"
            save_results = True
        [[flat_field]]
        [[sky_sub]]
        [[assign_wcs]]
            skip = False
    """
    config_file = str(tmp_path / "test_config.cfg")
    with open(config_file, "w") as f:
        f.write(conf)

    # Create a temporary dark config file
    conf = """
    class = "liger_iris_pipeline.DarkSubtraction"
    """
    config_file_dark = str(tmp_path / "dark_config.cfg")
    with open(config_file_dark, "w") as f:
        f.write(conf)

    # Files
    remote_sci_L1_filename = 'IRIS/L1/2024B-P123-008_IRIS_IMG1_SCI-J1458+1013-Y-4.0_LVL1_0001-00.fits'
    remote_sky_L1_filename = 'IRIS/L1/2024B-P123-008_IRIS_IMG1_SKY-J1458+1013-Y-4.0_LVL1_0001-00.fits'
    sci_L1_filename = download_osf_file(remote_sci_L1_filename, use_cached=True)
    sky_bkg_L1_filename = download_osf_file(remote_sky_L1_filename, use_cached=True)
    sci_L1_filename_subarray = str(tmp_path / os.path.basename(sci_L1_filename.replace('-00.fits', '-01.fits')))

    # Load the science model
    input_model = datamodels.ImagerModel(sci_L1_filename)

    # Subarray params
    yc, xc = int(input_model.data.shape[0] / 2), int(input_model.data.shape[1] / 2)
    xstart = xc - 50
    ystart = yc - 50
    xsize = 100
    ysize = 100
    input_model.meta.subarray.id = 1
    input_model.meta.subarray.name = "CUSTOM"
    input_model.meta.subarray.xstart = xstart + 1 # zero index
    input_model.meta.subarray.ystart = ystart + 1 # zero index
    input_model.meta.subarray.xsize = xsize
    input_model.meta.subarray.ysize = ysize

    # Subarray indices
    subarray_slice = np.s_[ystart:ystart+ysize, xstart:xstart+xsize]

    # Slice the data
    input_model.data = np.array(input_model.data[subarray_slice])
    input_model.err = np.array(input_model.err[subarray_slice])
    input_model.dq = np.array(input_model.dq[subarray_slice])

    # Save the subarray model
    input_model.save(sci_L1_filename_subarray)

    # ASN
    # asn = L1Association.from_product(
    # {
    #     "members": [
    #         {
    #             "expname": sci_L1_filename_subarray,
    #             "exptype": "SCI",
    #         },
    #         {
    #             "expname": sky_bkg_L1_filename,
    #             "exptype": "SKY"
    #         }
    #     ]
    # })
    input = {
        "SCI": sci_L1_filename_subarray,
        "SKY": sky_bkg_L1_filename,
    }

    # Call pipeline with test ASN
    pipeline = liger_iris_pipeline.ImagerStage2Pipeline(config_file=config_file)
    model_result = pipeline.run(input, output_dir=str(tmp_path))

    # Manual L2
    # Everntually update this to use a static result
    with datamodels.open(pipeline.dark_sub.dark_filename) as dark_model, \
        datamodels.open(pipeline.flat_field.flat_filename) as flat_model, \
        datamodels.open(sci_L1_filename_subarray) as sci_model, \
        datamodels.open(sky_bkg_L1_filename) as bkg_model:
        ref_data = (sci_model.data - dark_model.data[subarray_slice]) / flat_model.data[subarray_slice] - bkg_model.data[subarray_slice]
        np.testing.assert_allclose(model_result.data, ref_data, rtol=1e-6)