import numpy as np
import scipy.stats

from liger_iris_pipeline.normalize import NormalizeStep
from liger_iris_pipeline import datamodels

from .utils import make_imager_model

def test_normalize_step():

    shape = (100, 100)
    
    input_model = make_imager_model(
        shape=shape,
        snr=100,
    )
    input_model.data[input_model.data.shape[0]//2, :] = 0.6  # for mode calc

    # Loop over methods
    for method in [None, "mean", "median", "mode"]:
        
        # Test NormalizeStep class
        step_output = NormalizeStep.call(input_model, method=method)

        # Expected output
        if method is None:
            expected_output_data = input_model.copy().data
        elif method == "mean":
            expected_output_data = input_model.data / np.mean(input_model.data)
        elif method == "median":
            expected_output_data = input_model.data / np.median(input_model.data)
        elif method == "mode":
            expected_output_data = (
                input_model.data / scipy.stats.mode(input_model.data, axis=None).mode
            )

        # Test
        np.testing.assert_allclose(
            step_output.data,
            expected_output_data,
            rtol=1e-6
        )
