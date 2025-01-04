# Imports
import numpy as np
import liger_iris_pipeline
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.tests.test_utils import add_meta_data

def create_config():
    conf = """
    name = "ImagerStage2Pipeline"
    class = "liger_iris_pipeline.pipeline.CreateFlatfield"
    save_results = True

    [steps]
        [[dark_sub]]
        [[normalize]]
            method = "median"
    """
    return conf


def test_create_flat(tmp_path):

    # Grab flat field
    raw_flat_filename = str(tmp_path / "2024A-P123-044_IRIS_IMG1_FLAT-Y_LVL1_0001-00.fits")
    meta = {
        'model_type' : 'ImagerModel',
        'target.name': 'FLAT',
        'target.ra' : 0.0,
        'target.dec' : 0.0,
        'target.airmass_start' : 1.0,
        'exposure.itime' : 90,
        'exposure.nframes' : 1,
        'exposure.jd_start' : 2460577.5,
        'exposure.type' : 'FLAT',
        'instrument.name' : 'IRIS',
        'instrument.detector' : 'IMG1',
        'instrument.grating' : 'None',
        'instrument.mode' : 'IMG',
        'instrument.ifumode' : 'None',
        'instrument.filter' : 'Y',
        'instrument.scale' : 0.004,
    }

    # Create a simulated raw flat
    raw_flat_model = datamodels.ImagerModel(instrument='IRIS', data=np.random.normal(loc=1, scale=0.01, size=(4096, 4096)))
    add_meta_data(raw_flat_model, meta)
    raw_flat_model.save(raw_flat_filename)

    # ASN
    product ={
        "name": "Test",
        "members": [
            {
                "expname": raw_flat_filename,
                "exptype": "flat",
            },
        ]
    }

    # Create a temporary config file
    conf = create_config()
    config_file = tmp_path / "test_config.cfg"
    with open(config_file, "w") as f:
        f.write(conf)

    # Initialize flatfield pipeline
    flat_model, pipeline = liger_iris_pipeline.CreateFlatfield.call(product, config_file=config_file, return_step=True)

    # Open dark
    dark_model = datamodels.open(pipeline.dark_sub.dark_filename)

    # Manually create a dark subtracted master flat
    expected = raw_flat_model.data - dark_model.data
    expected /= np.median(expected)

    # Test
    np.testing.assert_allclose(flat_model.data, expected)