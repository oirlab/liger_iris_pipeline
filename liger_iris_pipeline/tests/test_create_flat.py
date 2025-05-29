# Imports
import numpy as np
import liger_iris_pipeline
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.tests.utils import get_meta, download_osf_file


def create_raw_flat(jd_start):
    data = np.full((2048, 2048), 2, dtype=np.float32) # 1 e-/s
    err = np.abs(np.random.normal(loc=0.01, scale=0.00005, size=data.shape))
    noise = err * np.random.randn(*data.shape)
    noise *= 0.01 / np.std(noise)
    data += noise
    data = np.clip(data, 0, np.inf)
    dq = np.zeros((2048, 2048), dtype=np.uint32)
    model = datamodels.ImagerModel(data=data, err=err, dq=dq)
    model.meta.instrument.name = 'Liger'
    model.meta.target.name = 'FLAT'
    model.meta.exposure.jd_start = jd_start
    model.meta.exposure.exposure_time = 180  # 3 minute exposure
    model.meta.exposure.exposure_type = 'FLAT'
    model.meta.instrument.mode = 'IMG'
    get_meta(model)
    return model


def test_create_flat():

    # Create a set of raw 2D flat frames
    times = np.linspace(2460577.5, 2460577.5 + 7/24, num=7)
    input = [create_raw_flat(jd_start) for jd_start in times]
    
    # Initialize and run step
    pipeline = liger_iris_pipeline.CreateFlatfield()
    pipeline.combine_frames.method = 'median'
    dark_filepath = download_osf_file('Liger/Cals/Liger_IMG_DARK_20240924000000_0.0.1.fits', use_cached=True)
    pipeline.dark_sub.dark = dark_filepath
    pipeline.combine_frames.error_calc = 'propagate'
    result = pipeline.run(input, save_result=False)

    # Test
    np.testing.assert_allclose(result.data, 1, rtol=1E-1)

    # Test model_blender
    assert result.meta.instrument.name == 'Liger'
    assert result.meta.exposure.jd_mid == np.mean([m.meta.exposure.jd_mid for m in input])
    assert result.meta.exposure.exposure_type == 'FLAT'
    assert result.meta.ref_type == 'flat'