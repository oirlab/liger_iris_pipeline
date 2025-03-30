
# See README.md for notes on testing data
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.tests.utils import download_osf_file


def test_load_liger_image():
    remote_sci_L1_filename = 'Liger/L1/2024B-P123-008_Liger_IMG_SCI-J1458+1013-Y-10.0_LVL1_0001-00.fits'
    sci_L1_filename = download_osf_file(remote_sci_L1_filename, use_cached=True)
    input_model = datamodels.open(sci_L1_filename)
    
    assert input_model.meta.model_type == "ImagerModel"
    assert input_model.schema_url == "https://oirlab.github.io/schemas/ImagerModel.schema"
    assert input_model.crds_observatory == "ligeriri"
    assert input_model.meta.organization == "WMKO"
    assert input_model.meta.telescope == "Keck-I"
    assert input_model.meta.instrument.name == "Liger"
    assert input_model.meta.instrument.detector == "IMG"
    assert input_model.meta.subarray.name == "FULL"
    assert input_model.data.shape == (2048, 2048)


def test_load_iris_image():
    remote_sci_L1_filename = 'IRIS/L1/2024B-P123-008_IRIS_IMG1_SCI-J1458+1013-Y-4.0_LVL1_0001-00.fits'
    sci_L1_filename = download_osf_file(remote_sci_L1_filename, use_cached=True)
    input_model = datamodels.open(sci_L1_filename)
    
    assert input_model.meta.model_type == "ImagerModel"
    assert input_model.schema_url == "https://oirlab.github.io/schemas/ImagerModel.schema"
    assert input_model.crds_observatory == "ligeriri"
    assert input_model.meta.organization == "TIO"
    assert input_model.meta.telescope == "TMT"
    assert input_model.meta.instrument.name == "IRIS"
    assert input_model.meta.instrument.detector == "IMG1"
    assert input_model.meta.subarray.name == "FULL"
    assert input_model.data.shape == (4096, 4096)