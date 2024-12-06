
# See README.md for notes on testing data
from liger_iris_pipeline.tests.test_utils import get_data_from_url
from liger_iris_pipeline import ImagerModel

def test_load_liger_image():

    #raw_science_filename = get_data_from_url("48191524")
    raw_science_filename = "/Users/cale/Desktop/Liger_Test_Data/raw_frame_sci_20240805.fits"
    
    input_model = ImagerModel(raw_science_filename)
    
    assert input_model.meta.model_type == "ImagerModel"
    assert input_model.crds_observatory == "ligeriri"
    assert input_model.meta.telescope == "Keck"
    assert input_model.meta.instrument.name == "Liger"
    assert input_model.meta.subarray.name == "FULL"
    assert input_model.data.shape == (2048, 2048)

def test_load_iris_image():

    #raw_science_filename = get_data_from_url("48191524")
    raw_science_filename = "/Users/cale/Desktop/IRIS_Test_Data/raw_frame_sci_20240805.fits"
    input_model = ImagerModel(raw_science_filename)
    
    assert input_model.meta.model_type == "ImagerModel"
    assert input_model.crds_observatory == "ligeriri"
    assert input_model.meta.telescope == "TMT"
    assert input_model.meta.instrument.name == "IRIS"
    assert input_model.meta.subarray.name == "FULL"
    assert input_model.data.shape == (4096, 4096)