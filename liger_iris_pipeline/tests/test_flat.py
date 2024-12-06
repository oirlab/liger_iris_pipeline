# Imports
import liger_iris_pipeline
import numpy as np

# See README.md for notes on testing data
from liger_iris_pipeline.tests.test_utils import get_data_from_url


def test_flat():

    # Downlaod and open the raw science frame
    #raw_science_filename = get_data_from_url("48191524")
    raw_science_filename = "/Users/cale/Desktop/IRIS_Test_Data/raw_frame_sci_20240805.fits"
    input_model = liger_iris_pipeline.ImagerModel(raw_science_filename)

    # Download the raw flat frame
    #raw_flat_filename = get_data_from_url("48191521")
    raw_flat_filename = "/Users/cale/Desktop/IRIS_Test_Data/raw_frame_flat_20240805.fits"

    # Flatfield pipeline (generates the median flat)
    pipeline = liger_iris_pipeline.pipeline.ProcessFlatfield()
    flatfield = pipeline.run(raw_flat_filename)[0]

    # Flatfield step (performs flatfield correction) using the CRDS retrieved flat
    step = liger_iris_pipeline.FlatFieldStep()
    step_output = step.run(raw_science_filename)

    # Test the step output is the same as the the manual correction
    np.testing.assert_allclose(step_output.data, input_model.data / flatfield.data)