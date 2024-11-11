# Imports
import liger_iris_pipeline

liger_iris_pipeline.monkeypatch_jwst_datamodels()
from liger_iris_pipeline.normalize.normalize import do_correction
import numpy as np
import scipy.stats


def test_normalize():
    # Create an test image with a specified row
    input_model = liger_iris_pipeline.datamodels.LigerIrisImageModel(
        data=np.random.rand(4096, 4096)
    )
    input_model.data[3, :] = 0.6  # for mode calc

    # Loop over methods
    for method in [None, "mean", "median", "mode"]:
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

        # Test do_correction method
        output = do_correction(input_model, method=method)
        np.testing.assert_allclose(output.data, expected_output_data, rtol=1e-6)


def test_normalize_step():
    # Create an test image
    input_model = liger_iris_pipeline.datamodels.LigerIrisImageModel(
        data=np.random.rand(4096, 4096)
    )
    input_model.data[3, :] = 0.6  # for mode calc

    # Loop over methods
    for method in [None, "mean", "median", "mode"]:
        # Test NormalizeStep class
        step = liger_iris_pipeline.normalize.NormalizeStep(method=method)
        step_output = step.run(input_model)

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
        np.testing.assert_allclose(step_output.data, expected_output_data, rtol=1e-6)
