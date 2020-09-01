import json
import pytest
import numpy as np
import warnings
import os
from astropy.utils import data
from jwst.associations import load_asn

import iris_pipeline

iris_pipeline.monkeypatch_jwst_datamodels()

from iris_pipeline.tests.test_utils import get_data_from_url

def test_image2():
    with open("iris_pipeline/tests/data/asn_subtract_bg_flat.json") as fp:
        asn = load_asn(fp)
    raw_science_filename = get_data_from_url("17903858")
    raw_background_filename = get_data_from_url("17903855")
    asn["products"][0]["members"][0]["expname"] = raw_science_filename
    asn["products"][0]["members"][1]["expname"] = raw_background_filename
    with open("test_asn.json", "w") as out_asn:
        json.dump(asn, out_asn)
    iris_pipeline.pipeline.ProcessImagerL2Pipeline.call("test_asn.json", config_file="iris_pipeline/tests/data/image2_iris.cfg")
    ref_filename = get_data_from_url("17905553")
    with iris_pipeline.datamodels.IRISImageModel("test_iris_subtract_bg_flat_cal.fits") as out, \
         iris_pipeline.datamodels.IRISImageModel(ref_filename) as ref:
        np.testing.assert_allclose(out.data, ref.data, rtol=1e-6)

def test_image2_subarray(tmp_path):
    with open("iris_pipeline/tests/data/asn_subtract_bg_flat.json") as fp:
        asn = load_asn(fp)
    raw_science_filename = get_data_from_url("17903858")
    input_model = iris_pipeline.datamodels.IRISImageModel(raw_science_filename)

    xstart = 100
    ystart = 200
    xsize = 50
    ysize = 60
    input_model.meta.subarray.name = "CUSTOM"
    input_model.meta.subarray.xstart = xstart + 1
    input_model.meta.subarray.ystart = ystart + 1
    input_model.meta.subarray.xsize = xsize
    input_model.meta.subarray.ysize = ysize
    subarray_slice = np.s_[ystart:ystart+ysize, xstart:xstart+xsize]

    input_model.data = np.array(input_model.data[subarray_slice])
    input_model.dq = np.array(input_model.dq[subarray_slice])
    input_model.err = np.array(input_model.err[subarray_slice])

    raw_science_subarray_filename = tmp_path / "temp_subarray_science.fits"
    input_model.write(raw_science_subarray_filename)

    raw_background_filename = get_data_from_url("17903855")
    asn["products"][0]["members"][0]["expname"] = str(raw_science_subarray_filename)
    asn["products"][0]["members"][1]["expname"] = raw_background_filename
    with open("test_asn.json", "w") as out_asn:
        json.dump(asn, out_asn)
    iris_pipeline.pipeline.ProcessImagerL2Pipeline.call("test_asn.json", config_file="iris_pipeline/tests/data/image2_iris.cfg")
    ref_filename = get_data_from_url("17905553")
    with iris_pipeline.datamodels.IRISImageModel("test_iris_subtract_bg_flat_cal.fits") as out, \
         iris_pipeline.datamodels.IRISImageModel(ref_filename) as ref:
        np.testing.assert_allclose(out.data, ref.data[subarray_slice], rtol=1e-6)

if __name__ == "__main__":
    test_image2()
