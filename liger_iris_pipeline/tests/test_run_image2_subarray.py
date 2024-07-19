# Imports
import liger_iris_pipeline
liger_iris_pipeline.monkeypatch_jwst_datamodels()
from liger_iris_pipeline.parse_subarray_map.parse_subarray_map_step import parse_subarray_map
from liger_iris_pipeline import ProcessImagerL2Pipeline
from liger_iris_pipeline.datamodels import LigerIrisImageModel
from test_utils import get_data_from_url
import numpy as np
import textwrap
from astropy.io import fits

def test_run_image2_subarray():

    # Download the raw image
    raw_science_subarray_filename = get_data_from_url("21942483")
    fits.setval(raw_science_subarray_filename, keyword='DATAMODL', value='LigerIrisImageModel', ext=0)
    raw_science_frame = LigerIrisImageModel(raw_science_subarray_filename)

    # Ensure datamodel attributes are correct
    assert raw_science_frame.meta.subarray.name == "CUSTOM"
    assert raw_science_frame.meta.subarray.xsize == 40

    # Create a temp config file
    cfg_str = textwrap.dedent(
        """\
        name = "ProcessImagerL2Pipeline"
        class = "liger_iris_pipeline.pipeline.ProcessImagerL2Pipeline"
        save_results = True

        [steps]
        [[bkg_subtract]]
        [[assign_wcs]]
            skip = True
        [[dark_current]]
        [[flat_field]]
        [[photom]]
            skip = True
        [[resample]]
            skip = True\
        """
    )
    with open("temp_image2_subarray.cfg", "w+") as f:
        f.write(cfg_str)

    # Create and run the pipeline
    pipeline = ProcessImagerL2Pipeline(config_file="temp_image2_subarray.cfg")
    result = pipeline.run(raw_science_subarray_filename)

    # Assert data 
    assert int(result[0].data.min()) == 34
    assert int(result[0].data.max()) == 6232


test_run_image2_subarray()