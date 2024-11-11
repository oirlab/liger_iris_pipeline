import liger_iris_pipeline

# See README.md for notes on testing data
from liger_iris_pipeline.tests.test_utils import get_data_from_url

from liger_iris_pipeline.datamodels import LigerImagerModel


def test_load_liger_image_file():

    #raw_science_filename = get_data_from_url("48191524")
    raw_science_filename = "/Users/cale/Desktop/Liger_Test_Data/"

    input_model = LigerImagerModel(raw_science_filename)
    
    assert input_model.crds_observatory == "ligeriri"
    assert input_model.meta.instrument.name == "Liger"
    assert input_model.data.shape == (2048, 2048)
