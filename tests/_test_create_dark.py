# Imports
import numpy as np
from liger_iris_pipeline import CreateDarkPipeline
from .utils import make_dark_model

def test_create_dark():

    # Create a set of raw 2D dark frames
    mjds = np.linspace(2460577.5, 2460577.5 + 7/24, num=7) - 2400000.5
    dark_current = 0.01
    snr = 100
    input = []
    for mjd in mjds:
        input.append(
            make_dark_model(
                dark_current=dark_current,
                snr=snr,
                instrument_name='Liger',
                meta={'instrument.mode': 'IMG'},
                shape=(100, 100)
            )
        )
    
    # Initialize and run step
    result = CreateDarkPipeline.call(input)

    # Test data
    np.testing.assert_allclose(result.data.mean(), dark_current, rtol=1E-4)

    # Test model_blender
    assert result.meta.instrument.name == 'Liger'
    assert result.meta.exposure.mjd_start == np.min([m.meta.exposure.mjd_start for m in input])
    assert result.meta.exposure.type == 'DARK'
    assert result.meta.ref_type == 'dark'