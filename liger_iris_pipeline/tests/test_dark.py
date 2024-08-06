# Imports
import liger_iris_pipeline
liger_iris_pipeline.monkeypatch_jwst_datamodels()
import numpy as np
from liger_iris_pipeline.tests.test_utils import get_data_from_url
from jwst import datamodels
from liger_iris_pipeline.dark_current.dark_sub import do_correction

def test_dark_subtraction():
    # Grab simulated raw frame
    raw_science_filename = get_data_from_url("48191524")
    input_model = datamodels.open(raw_science_filename)

    # Create a dark image with randomized vals centered around zero
    dark_model = liger_iris_pipeline.datamodels.DarkModel(data=np.random.normal(size=(4096, 4096)))

    # Manual subtraction
    expected_output_data = input_model.data - dark_model.data

    # Test do_correction method
    output = do_correction(input_model, dark_model)
    np.testing.assert_allclose(output.data, expected_output_data)

def test_dark_step():
    raw_science_filename = get_data_from_url("48191524")
    input_model = datamodels.open(raw_science_filename)

    # Test DarkCurrentStep class
    step = liger_iris_pipeline.dark_current.DarkCurrentStep()
    step_output = step.run(raw_science_filename)
    step_dark_model = datamodels.open(step.dark_name)

    # Test
    np.testing.assert_allclose(step_output.data, input_model.data - step_dark_model.data)
