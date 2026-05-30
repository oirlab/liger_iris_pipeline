# Imports
import numpy as np
from liger_iris_pipeline import CreateDetectorFlatPipeline
from .utils import make_detector_flat_model, make_dark_model

def test_create_flat():

    # Create a set of raw 2D flat frames
    mjds = np.linspace(2460577.5, 2460577.5 + 7/24, num=7) - 2400000.5
    snr = 100
    input = []
    for mjd in mjds:
        input.append(
            make_detector_flat_model(
                snr=snr,
                instrument_name='Liger',
                meta={'instrument.mode': 'IMG'},
                shape=(100, 100)
            )
        )

    dark_model = make_dark_model(
        dark_current=0.01,
        snr=1000,
        instrument_name='Liger',
        meta={'instrument.mode': 'IMG'},
        shape=(100, 100)
    )
    
    # Initialize and run step
    result = CreateDetectorFlatPipeline.call(input, steps={'dark_sub': {'dark': dark_model}})

    # Test data
    np.testing.assert_allclose(result.data.mean(), 1, rtol=1E-4)

    # Test model_blender
    assert result.meta.instrument.name == 'Liger'
    assert result.meta.exposure.mjd_start == np.min([m.meta.exposure.mjd_start for m in input])
    assert result.meta.exposure.exposure_type == 'DETFLAT'
    assert result.meta.ref_type == 'detflat'