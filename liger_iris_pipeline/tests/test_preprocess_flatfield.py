# Imports
import liger_iris_pipeline
import numpy as np
from astropy.io import fits

# See README.md for notes on testing data
from liger_iris_pipeline.tests.test_utils import get_data_from_url
from liger_iris_pipeline import datamodels

def test_process_flatfield():

    # Grab flat field
    #raw_flat_filename = get_data_from_url("48191521")
    raw_flat_filename = "/Users/cale/Desktop/IRIS_Test_Data/raw_frame_flat_20240805.fits"
    input_model = datamodels.open(raw_flat_filename)

    # Initialize flatfield pipeline
    pipeline = liger_iris_pipeline.ProcessFlatfield()

    # Run pipeline
    pipeline_output = pipeline.run(raw_flat_filename)

    # Open dark
    dark_current = datamodels.open(pipeline.dark_current.dark_name)

    # Manually create a dark subtracted master flat
    expected = input_model.data - dark_current.data
    expected /= np.median(expected)

    # Test
    np.testing.assert_allclose(pipeline_output[0].data, expected)