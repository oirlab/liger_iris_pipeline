
import numpy as np
from liger_iris_pipeline import datamodels, FlatFieldStep
from liger_iris_pipeline.utils.gdrive import download_gdrive_file

def test_flat_step():
    sci_L1_filepath = download_gdrive_file('Liger/L1/2024B-P001-001_Liger_IMG_SCI_LVL1_0001_M13-J-10mas.fits', use_cached=True)
    flat_filepath = download_gdrive_file('Liger/Cals/Liger_IMG_FLAT_20240924000000_0.0.1.fits', use_cached=True)
    step = FlatFieldStep()
    step_output = step.run(sci_L1_filepath, flat=flat_filepath)
    flat_model = datamodels.open(step.flat_filepath)
    input_model = datamodels.open(sci_L1_filepath)
    np.testing.assert_allclose(step_output.data, input_model.data / flat_model.data)