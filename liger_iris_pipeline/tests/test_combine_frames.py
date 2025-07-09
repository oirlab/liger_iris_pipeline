# Imports
import numpy as np
import liger_iris_pipeline
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.tests.utils import get_meta


def create_frame(jd_start, itime):
    data = np.ones((4096, 4096), dtype=np.float32) # 1 e-/s
    err = np.abs(np.random.normal(loc=0.01, scale=0.00005, size=data.shape))
    noise = err * np.random.randn(*data.shape)
    noise *= 0.01 / np.std(noise)
    data += noise
    data = np.clip(data, 0, None)
    dq = np.zeros((4096, 4096), dtype=np.uint32)
    model = datamodels.ImagerModel(data=data, err=err, dq=dq)
    model.meta.instrument.name = 'Liger'
    model.meta.instrument.mode = 'IMG'
    model.meta.instrument.filter = 'J'
    model.meta.exposure.jd_start = jd_start
    model.meta.exposure.exposure_time = itime
    get_meta(model)
    return model


def test_combine_frames():

    # Create a set of frames
    times = np.arange(2460577.5, 2460577.5 + 7, 1)
    models = [create_frame(jd_start, itime=300) for jd_start in times]

    # Intentionally add a bad pixel
    models[0].data[0, 0] *= 0.1
    
    # Initialize and run step
    step = liger_iris_pipeline.CombineFramesStep(method='median')
    result = step.run(models, save_result=False, error_calc='propagate')

    # Test data
    np.testing.assert_allclose(result.data, 1, rtol=1E-1)

    # Test model_blender
    assert result.meta.instrument.name == 'Liger'
    assert result.meta.exposure.jd_mid == np.mean([m.meta.exposure.jd_mid for m in models])