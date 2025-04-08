# Imports
import numpy as np
import liger_iris_pipeline
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.tests.utils import add_meta_data


def create_frame(jd_start):
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
        'target.name': 'MYTARGET',
        'target.ra' : 0.0,
        'target.dec' : 0.0,
        'target.airmass_start' : 1.0,
        'exposure.exposure_time' : 90,
        'exposure.nframes' : 1,
        'exposure.jd_start' : jd_start,
        'exposure.type' : 'SCI',
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


def test_combine_frames():

    # Create a set of frames
    times = np.arange(2460577.5, 2460577.5 + 7, 1)
    models = [create_frame(jd_start) for jd_start in times]

    # Intentionally add a bad pixel
    models[0].data[0, 0] *= 0.1
    
    # Initialize and run step
    step = liger_iris_pipeline.CombineFramesStep(method='median')
    result = step.run(models, save_result=False, error_calc='propagate')

    # Test data
    np.testing.assert_allclose(result.data, 1, rtol=1E-1)

    # Test model_blender
    assert result.meta.instrument.name == 'IRIS'
    assert result.meta.exposure.jd_mid == np.mean([m.meta.exposure.jd_mid for m in models])