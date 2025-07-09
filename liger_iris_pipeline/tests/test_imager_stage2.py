# Imports
import liger_iris_pipeline
import liger_iris_pipeline.datamodels as datamodels
import numpy as np
from liger_iris_pipeline.utils.gdrive import download_gdrive_file

def test_imager_stage2(tmp_path):

    sci_L1_filepath = download_gdrive_file('Liger/L1/2024B-P001-001_Liger_IMG_SCI_LVL1_0001_M13-J-10mas-skyscale1.0.fits', use_cached=True)
    dark_filepath = download_gdrive_file('Liger/Cals/Liger_IMG_DARK_20240924000000_0.0.1.fits', use_cached=True)
    flat_filepath = download_gdrive_file('Liger/Cals/Liger_IMG_FLAT_20240924000000_0.0.1.fits', use_cached=True)
    input = {
        "SCI": [sci_L1_filepath],
    }

    # Create and call the pipeline object
    pipeline = liger_iris_pipeline.ImagerStage2Pipeline()
    pipeline.dark_sub.dark = dark_filepath
    pipeline.flat_field.flat = flat_filepath
    results = pipeline.run(input)

    # Manual L2 calculation
    for sci_input, sci_output_model in zip(input['SCI'], results):
        with datamodels.open(pipeline.dark_sub.dark_filepath) as dark_model, \
            datamodels.open(pipeline.flat_field.flat_filepath) as flat_model, \
            datamodels.open(sci_input) as sci_input_model, \
            datamodels.open(pipeline.background_sub.background) as bkg_model:
            ref_data = (sci_input_model.data - dark_model.data) / flat_model.data - bkg_model.data
            np.testing.assert_allclose(sci_output_model.data, ref_data, rtol=1e-6)