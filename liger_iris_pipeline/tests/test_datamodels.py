import liger_iris_pipeline
from .test_utils import get_data_from_url
from liger_iris_pipeline.datamodels import LigerIrisImageModel


def test_load_iris_image_file():

    raw_science_filename = get_data_from_url("48191524")

    input_model = LigerIrisImageModel(raw_science_filename)

    assert input_model.meta.instrument.name == "IRIS"
    assert input_model.data.shape == (4096, 4096)
