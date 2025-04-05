# Imports
import numpy as np
import liger_iris_pipeline
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.tests.utils import add_meta_data


def create_raw_dark(jd_start):
    data = np.ones((4096, 4096), dtype=np.float32) # 1 e-/s
    err = np.abs(np.random.normal(loc=0.01, scale=0.00005, size=data.shape))
    noise = err * np.random.randn(*data.shape)
    noise *= 0.01 / np.std(noise)
    data += noise
    data = np.clip(data, 0, np.inf)
    dq = np.zeros((4096, 4096), dtype=np.uint32)
    model = datamodels.ImagerModel(data=data, err=err, dq=dq)
    meta = {
        'model_type' : 'ImagerModel',
        'target.name': 'DARK',
        'target.ra' : 0.0,
        'target.dec' : 0.0,
        'target.airmass_start' : 1.0,
        'exposure.exposure_time' : 3600,
        'exposure.nframes' : 1,
        'exposure.jd_start' : jd_start,
        'exposure.type' : 'DARK',
        'instrument.name' : 'IRIS',
        'instrument.detector' : 'IMG1',
        'instrument.grating' : 'None',
        'instrument.mode' : 'IMG',
        'instrument.ifumode' : 'None',
        'instrument.filter' : 'Y',
        'instrument.scale' : 0.004,
    }
    add_meta_data(model, meta)
    return model


def test_create_dark():

    # Create a set of raw 2D dark frames
    times = np.linspace(2460577.5, 2460577.5 + 7/24, num=7)
    input = [create_raw_dark(jd_start) for jd_start in times]
    
    # Initialize and run step
    pipeline = liger_iris_pipeline.CreateDark()
    pipeline.combine_frames.method = 'median'
    pipeline.combine_frames.error_calc = 'propagate'
    result = pipeline.run(input, save_result=False)

    # Test data
    np.testing.assert_allclose(result.data, 1, rtol=1E-1)

    # Test model_blender
    assert result.meta.instrument.name == 'IRIS'
    assert result.meta.exposure.jd_mid == np.mean([m.meta.exposure.jd_mid for m in input])
    assert result.meta.exposure.type == 'DARK'
    assert result.meta.reftype == 'dark'

test_create_dark()