import numpy as np
from liger_iris_pipeline.coadd import CoaddFramesStep
from liger_iris_pipeline import datamodels

from .utils import make_imager_model

def test_coadd_frames():

    np.random.seed(1)

    # Create a set of frames
    input = []
    ny, nx = 100, 100
    snr = 100
    truth = snr**2
    n_frames = 11
    mjds = np.linspace(2460577.5, 2460577.5 + 7/24, num=n_frames) - 2400000.5
    for mjd in mjds:
        model = make_imager_model(
            instrument_name='Liger',
            shape=(ny, nx),
            snr=snr,
            read_noise=1.0,
            meta={
                'exposure.mjd_start': mjd,
                'data_level' : '1'
            }
        )
        input.append(model)

    # Add a bad pixel to the first datamodel
    input[0].data[0, 0] *= 0.5
    
    # Test all methods
    methods = ['mean', 'median', 'wmean', 'wmedian']
    for method in methods:

        print(f"Testing method: {method}")

        step = CoaddFramesStep(
            method=method,
            sigma_thresh_low=5,
            sigma_thresh_high=5,
            do_sigma_clip=True,
        )
        model_result = step.run(input)

        # Test accuracy
        rel_residuals = np.abs(model_result.data - truth) / model_result.err
        assert np.sum(rel_residuals > 5) == 0

        # Test 1 sigma statistics
        confidence_level = np.sum(rel_residuals < 1) / rel_residuals.size

        # Median not as accurate
        if method in ('median', 'wmedian'):
            assert abs(confidence_level - 0.683) < 0.2
        else:
            assert abs(confidence_level - 0.683) < 0.1