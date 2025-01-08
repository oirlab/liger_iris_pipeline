
import numpy as np
import liger_iris_pipeline
from liger_iris_pipeline import datamodels

def test_dark_step(tmp_path):
    sci_L1_filename = "liger_iris_pipeline/tests/data/2024B-P123-008_IRIS_IMG1_SCI-J1458+1013-Y-4.0_LVL1_0001-00.fits"
    input_model = datamodels.open(sci_L1_filename)

    # For dev purposes, no config for real/final test
    conf = """
    class = "liger_iris_pipeline.DarkSubtractionStep"
    output_dir = "/Users/cale/Desktop/DRS_Testing/"
    """
    config_file = str(tmp_path / "test_dark_config.cfg")
    with open(config_file, "w") as f:
        f.write(conf)

    step = liger_iris_pipeline.DarkSubtractionStep(config_file=config_file)
    step_output = step.run(sci_L1_filename)
    dark_model = datamodels.open(step.dark_filename)

    np.testing.assert_allclose(step_output.data, input_model.data - dark_model.data)

# from pathlib import Path
# tmp_path = Path("/Users/cale/Desktop/DRS_Testing/")
# test_dark_step(tmp_path)