import os

from liger_iris_pipeline import datamodels
import numpy as np

def make_test_image(instrument_name : str, shape : tuple[int, int]):
    data = np.ones(shape)
    meta = {
        'instrument.name' : instrument_name,
        'instrument.mode' : 'IMG',
        'target.ra': 0.0,
        'target.dec': 0.0,
        'instrument.scale' : 0.01,
        'instrument.filter': 'KN2',
        'data_level': '1',
    }
    return datamodels.ImagerModel(data=data, meta=meta)


def _test_data_attrs(model):
    assert np.array_equal(model.data, np.ones(model.shape))
    assert np.array_equal(model.err, np.zeros(model.shape))
    assert np.array_equal(model.var_poisson, np.zeros(model.shape))
    assert np.array_equal(model.var_rnoise, np.zeros(model.shape))
    assert np.array_equal(model.dq, np.zeros(model.shape))
    assert model.receipt is not None
    assert model.calibrations is not None
    if model.meta.instrument.name == "IRIS":
        assert model.subarray_map is not None
    else:
        assert model.subarray_map is None


def test_liger_image(tmp_path):
    
    shape = (2048, 2048)
    model = make_test_image(instrument_name="Liger", shape=shape)
    output_path = str(tmp_path / "test_imager_model.fits")
    model.save(output_path=output_path)
    model = datamodels.open(output_path)

    # Test meta attrs
    assert model.meta.filename == os.path.basename(output_path)
    assert model.meta.model_type == "ImagerModel"
    assert model.meta.telescope == "Keck-I"
    assert model.instrument_name == "Liger"
    assert model.meta.instrument.detector == "IMG"
    assert model.meta.instrument.filter == "KN2"
    assert model.shape == shape

    # Test data attrs
    _test_data_attrs(model)


def test_iris_image(tmp_path):

    shape = (4096, 4096)
    model = make_test_image(instrument_name="IRIS", shape=shape)
    output_path = str(tmp_path / "test_imager_model.fits")
    model.save(output_path=output_path)
    model = datamodels.open(output_path)

    # Test meta attrs
    assert model.meta.filename == os.path.basename(output_path)
    assert model.meta.model_type == "ImagerModel"
    assert model.meta.telescope == "TMT"
    assert model.instrument_name == "IRIS"
    assert model.meta.instrument.detector == "IMG1"
    assert model.meta.instrument.filter == "KN2"
    assert model.meta.subarray.name == "FULL"
    assert model.shape == shape

    # Test data attrs
    _test_data_attrs(model)