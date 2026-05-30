import numpy as np
from liger_iris_pipeline.coadd import CoaddFramesStep
from liger_iris_pipeline import datamodels

from .utils import make_imager_model

def test_model_blender():

    # Create a set of frames
    mjds = np.linspace(2460577.5, 2460577.5 + 7/24, num=7) - 2400000.5
    input = []
    ny, nx = 2, 2
    for mjd in mjds:
        model = make_imager_model(
            instrument_name='Liger',
            shape=(ny, nx),
            snr=100,
            read_noise=1.0,
            meta={
                'exposure.mjd_start': mjd,
                'exposure.exposure_time': 60.0,
                'data_level' : '1'
            }
        )
        model.generate_filename()
        input.append(model)

        # Blend models
        result = datamodels.ImagerModel.from_datamodels(input)

        # Test model_blender
        assert result.meta.instrument.name == 'Liger'
        assert result.meta.exposure.mjd_start == np.min([m.meta.exposure.mjd_start for m in input])
        assert result.meta.exposure.exposure_time == np.sum([m.meta.exposure.exposure_time for m in input])

        # Test HDRTAB (meta with blend_table: True)
        for m in input:
            assert m.meta.filename == result.hdrtab['FILENAME'][0]