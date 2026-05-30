from liger_iris_pipeline import __version__
from liger_iris_pipeline.dark_subtraction import DarkSubtractionStep
from .utils import make_imager_model
from liger_iris_pipeline import datamodels

import numpy as np

def test_dark_step(tmp_path):

    shape = (100, 100)

    # Models
    input_model = make_imager_model(shape=shape)
    #dark_model = make_dark_model(shape=shape)
    dark_current = 0.025  # electrons / sec / pixel
    dark_model = datamodels.DarkModel(
        data=np.full(shape, dark_current),
        meta={
            'instrument.mode' : 'IMG',
        }
    )
    dark_model.save(str(tmp_path / 'test_dark.fits'))

    # Setup and call the dark step
    model_result = DarkSubtractionStep.call(input_model.copy(), dark=dark_model)
    
    # Test against manual correction
    np.testing.assert_array_equal(
        model_result.data,
        input_model.data - dark_model.data
    )
    np.testing.assert_array_equal(
        model_result.err,
        np.sqrt(input_model.err**2 + dark_model.err**2)
    )
    np.testing.assert_array_equal(
        model_result.dq,
        input_model.dq | dark_model.dq
    )

    # Test that receipt table is updated
    receipt_table = model_result.receipt_table
    assert len(receipt_table) == 1
    assert receipt_table['CLASS'][0] == DarkSubtractionStep.__module__ + '.' + DarkSubtractionStep.__name__
    assert receipt_table['DRP_VERSION'][0] == __version__

    # Calibrations
    assert model_result.meta.cal_file.dark.filename == dark_model.meta.filename
    cal_table = model_result.calibrations_table
    assert cal_table[0]['FILENAME'] == dark_model.meta.filename

    # Status of step
    assert model_result.meta.step.dark_sub == 'COMPLETED' == receipt_table['STATUS'][0]