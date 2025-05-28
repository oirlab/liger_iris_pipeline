
# See README.md for notes on testing data
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.tests.utils import download_osf_file


def test_load_liger_image():
    sci_L1_filepath = download_osf_file('Liger/L1/2024B-P001-001_Liger_IMG_SCI_LVL1_0001_M13-J-10mas.fits', use_cached=True)
    model = datamodels.open(sci_L1_filepath)
    
    assert model.meta.model_type == "ImagerModel"
    assert model.schema_url == "https://oirlab.github.io/schemas/ImagerModel.schema"
    assert model.crds_observatory == "ligeriri"
    assert model.meta.telescope == "Keck-I"
    assert model.meta.instrument.name == "Liger"
    assert model.meta.instrument.detector == "IMG"
    assert model.data.shape == (2048, 2048)


def test_load_iris_image():
    sci_L1_filepath = download_osf_file('IRIS/L1/2024B-P001-001_IRIS_IMG1_SCI_LVL1_0001_M13-J-4mas.fits', use_cached=True)
    input_model = datamodels.open(sci_L1_filepath)
    
    assert input_model.meta.model_type == "ImagerModel"
    assert input_model.schema_url == "https://oirlab.github.io/schemas/ImagerModel.schema"
    assert input_model.crds_observatory == "ligeriri"
    assert input_model.meta.telescope == "TMT"
    assert input_model.meta.instrument.name == "IRIS"
    assert input_model.meta.instrument.detector == "IMG1"
    assert input_model.meta.subarray.name == "FULL"
    assert input_model.data.shape == (4096, 4096)