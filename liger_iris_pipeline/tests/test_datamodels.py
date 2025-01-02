
# See README.md for notes on testing data
from liger_iris_pipeline import ImagerModel

def test_load_liger_image():
    sci_L1_filename = "/Users/cale/Desktop/Liger_IRIS_Test_Data/Liger/2024A-P123-044_Liger_IMG_SCI-J1458+1013-SIM-Y_LVL1_0001-00.fits"
    input_model = ImagerModel(sci_L1_filename)
    
    assert input_model.meta.model_type == "ImagerModel"
    assert input_model.schema_url == "https://oirlab.github.io/schemas/LigerImagerModel.schema"
    assert input_model.crds_observatory == "ligeriri"
    assert input_model.meta.organization == "WMKO"
    assert input_model.meta.telescope == "Keck-I"
    assert input_model.meta.instrument.name == "Liger"
    assert input_model.meta.instrument.detector == "IMG"
    assert input_model.meta.subarray.name == "FULL"
    assert input_model.data.shape == (2048, 2048)

def test_load_iris_image():
    sci_L1_filename = "/Users/cale/Desktop/Liger_IRIS_Test_Data/IRIS/2024A-P123-044_IRIS_IMG1_SCI-J1458+1013-SIM-Y_LVL1_0001-00.fits"
    input_model = ImagerModel(sci_L1_filename)
    
    assert input_model.meta.model_type == "ImagerModel"
    assert input_model.schema_url == "https://oirlab.github.io/schemas/IRISImagerModel.schema"
    assert input_model.crds_observatory == "ligeriri"
    assert input_model.meta.organization == "TIO"
    assert input_model.meta.telescope == "TMT"
    assert input_model.meta.instrument.name == "IRIS"
    assert input_model.meta.instrument.detector == "IMG1"
    assert input_model.meta.subarray.name == "FULL"
    assert input_model.data.shape == (4096, 4096)