# Imports
from liger_iris_pipeline import CalculateBackgroundImagerStep
from liger_iris_pipeline import SubtractBackgroundImagerStep
import liger_iris_pipeline.datamodels as datamodels
from liger_iris_pipeline.utils.gdrive import download_gdrive_file

import numpy as np


def test_calc_background_imager(tmp_path):

    # Science L1 files with sky gradients at different scales
    sky_scales = np.array([0.5, 0.75, 1.0, 1.25, 1.5])
    sci_files = [
        f"Liger/L1/2024B-P001-001_Liger_IMG_SCI_LVL1_0001_M13-J-10mas-skyscale{s}.fits"
        for s in sky_scales
    ]
    sci_files = [download_gdrive_file(f) for f in sci_files]
    sci_models = [datamodels.ImagerModel(f) for f in sci_files]
    for sci in sci_models:
        sci.data -= 0.025 # Remove constant dark current

    # Calculate the sky from a single science model
    step = CalculateBackgroundImagerStep()
    sky_model = step.run(sci_models[2])
    v = np.median(sky_model.data, axis=1)
    np.testing.assert_almost_equal(
        np.median(np.diff(v)) * sky_model.data.shape[0] / np.median(v),
        0.4,
        decimal=2,
        err_msg="Sky gradient does not match expected value."
    )

    # Calculate the scaled sky from a list of models
    step = CalculateBackgroundImagerStep()
    sky_model = step.run(sci_models)
    scales = step.background_result['sky_scales']
    np.testing.assert_almost_equal(
        step.background_result['sky_scales'],
        sky_scales,
        decimal=1,
        err_msg="Sky scales do not match expected values."
    )

    # Subtract the sky from the science models
    # NOTE: Add test if needed, otherwise this is just a sanity check that the step runs without error.
    for sci, scale in zip(sci_models, scales):
        step = SubtractBackgroundImagerStep()
        sci_sub = step.run(sci, background=sky_model, scale=scale)
