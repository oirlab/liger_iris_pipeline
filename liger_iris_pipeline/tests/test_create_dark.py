# Imports
import numpy as np
import liger_iris_pipeline
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.tests.utils import get_meta


def create_raw_dark(jd_start):
    data = np.ones((4096, 4096), dtype=np.float32) # 1 e-/s
    err = np.abs(np.random.normal(loc=0.01, scale=0.00005, size=data.shape))
    noise = err * np.random.randn(*data.shape)
    noise *= 0.01 / np.std(noise)
    data += noise
    data = np.clip(data, 0, None)
    dq = np.zeros((4096, 4096), dtype=np.uint32)
    model = datamodels.ImagerModel(data=data, err=err, dq=dq)
    model.meta.instrument.name = 'Liger'
    model.meta.target.name = 'DARK'
    model.meta.exposure.jd_start = jd_start
    model.meta.exposure.exposure_time = 3600  # 1 hour exposure
    model.meta.exposure.exposure_type = 'DARK'
    model.meta.instrument.mode = 'IMG'
    model.meta.instrument.filter = 'J'
    get_meta(model)
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
    assert result.meta.instrument.name == 'Liger'
    assert result.meta.exposure.jd_mid == np.mean([m.meta.exposure.jd_mid for m in input])
    assert result.meta.exposure.exposure_type == 'DARK'
    assert result.meta.ref_type == 'dark'