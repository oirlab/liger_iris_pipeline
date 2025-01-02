# Imports
import numpy as np
import os
import liger_iris_pipeline
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.tests.test_utils import add_meta_data
from liger_iris_pipeline.associations import IRISImagerL1Association

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
    raw_flat_model = datamodels.ImagerModel(instrument='IRIS', data=np.ones((4096, 4096)))
    add_meta_data(raw_flat_model, meta)
    raw_flat_model.save(raw_flat_filename)

    # ASN
    asn_file = str(tmp_path / 'temp_asn.json')
    output_file = datamodels.ReferenceFileModel.generate_filename(
        instrument='IRIS', detector='IMG1',
        reftype='FLAT', date='20250102T000000', version='0.0.1'
    )
    asn = IRISImagerL1Association.from_product({
        "name": output_file,
        "members": [
            {
                "expname": raw_flat_filename,
                "exptype": "flat",
            },
        ]
    })
    asn.dump(asn_file)

    # Initialize flatfield pipeline
    model_result, pipeline = liger_iris_pipeline.CreateFlatfield.call(asn_file, return_step=True)

    # Open dark
    dark_current = datamodels.open(pipeline.dark_current.dark_name)

    # Manually create a dark subtracted master flat
    expected = raw_flat_model.data - dark_current.data
    expected /= np.median(expected)

    # Test
    np.testing.assert_allclose(model_result.data, expected)


from pathlib import Path
test_create_flat(Path('/Users/Cale/Desktop/'))