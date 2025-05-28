# Imports
import liger_iris_pipeline
import liger_iris_pipeline.datamodels as datamodels
import numpy as np
import os
from liger_iris_pipeline.tests.utils import download_osf_file

def test_imager_stage2(tmp_path):

    sci_L1_filepath = download_osf_file('Liger/L1/2024B-P001-001_Liger_IMG_SCI_LVL1_0001_M13-J-10mas.fits', use_cached=True)
    sky_bkg_L1_filepath = download_osf_file('Liger/L1/2024B-P001-001_Liger_IMG_SKY_LVL1_0001_M13-J-10mas.fits', use_cached=True)
    dark_filepath = download_osf_file('Liger/Cals/Liger_IMG_DARK_20240924000000_0.0.1.fits', use_cached=True)
    flat_filepath = download_osf_file('Liger/Cals/Liger_IMG_FLAT_20240924000000_0.0.1.fits', use_cached=True)

    # Setup input
    input = {
        "SCI": sci_L1_filepath,
        "SKY": sky_bkg_L1_filepath,
    }

    # Create and call the pipeline object
    pipeline = liger_iris_pipeline.ImagerStage2Pipeline()
    pipeline.dark_sub.dark = dark_filepath
    pipeline.flat_field.flat = flat_filepath
    model_result = pipeline.run(input)

    # Manual L2 file
    with datamodels.open(pipeline.dark_sub.dark_filepath) as dark_model, \
        datamodels.open(pipeline.flat_field.flat_filepath) as flat_model, \
        datamodels.open(sci_L1_filepath) as sci_model, \
        datamodels.open(sky_bkg_L1_filepath) as bkg_model:
        ref_data = (sci_model.data - dark_model.data) / flat_model.data - bkg_model.data
        np.testing.assert_allclose(model_result.data, ref_data, rtol=1e-6)