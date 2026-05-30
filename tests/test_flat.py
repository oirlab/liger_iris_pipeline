
import numpy as np
from liger_iris_pipeline import DetectorFlatStep
from .utils import make_science_imager_model, make_detector_flat_model

def test_flat_step():

    # Models
    input_model = make_science_imager_model(shape=(100, 100))
    flat_model = make_detector_flat_model(shape=(100, 100))

    # Setup and call FlatFieldStep
    step_output = DetectorFlatStep.call(input_model.copy(), detflat=flat_model)

    # Test the data is correctly flat-fielded
    np.testing.assert_allclose(step_output.data, input_model.data / flat_model.data)
    np.testing.assert_allclose(step_output.var_poisson, input_model.var_poisson / flat_model.data)
    np.testing.assert_allclose(step_output.var_rnoise, input_model.var_rnoise / flat_model.data)