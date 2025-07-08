
import numpy as np
import liger_iris_pipeline
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.utils.gdrive import download_gdrive_file

def test_dark_step():
    sci_L1_filepath = download_gdrive_file('Liger/L1/2024B-P001-001_Liger_IMG_SCI_LVL1_0001_M13-J-10mas.fits', use_cached=True)
    dark_filepath = download_gdrive_file('Liger/Cals/Liger_IMG_DARK_20240924000000_0.0.1.fits', use_cached=True)
    input_model = datamodels.open(sci_L1_filepath)
    step = liger_iris_pipeline.DarkSubtractionStep()
    step_output = step.run(sci_L1_filepath, dark=dark_filepath)
    dark_model = datamodels.open(step.dark_filepath)
    np.testing.assert_allclose(step_output.data, input_model.data - dark_model.data)