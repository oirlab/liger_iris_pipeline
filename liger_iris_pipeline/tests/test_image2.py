# Imports
import liger_iris_pipeline
liger_iris_pipeline.monkeypatch_jwst_datamodels()
import numpy as np
from astropy.io import fits
from liger_iris_pipeline.tests.test_utils import get_data_from_url
from jwst import datamodels
import json
from jwst.associations import load_asn

def test_image2():

    # Load the association file
    with open("liger_iris_pipeline/tests/data/asn_subtract_bg_flat.json") as fp:
        asn = load_asn(fp)

    # Download the raw science frame
    raw_science_filename = get_data_from_url("48191524")

    # Download the master dark frame
    raw_dark_filename = get_data_from_url("48191518")

    # Sky backgorund???? (ref_filename below)
    raw_background_filename = '/Users/cale/Desktop/IRIS_Test_Data/test_iris_subtract_bg_flat_cal.fits'

    # Add science and dark to ASN
    asn["products"][0]["members"][0]["expname"] = raw_science_filename
    asn["products"][0]["members"][1]["expname"] = raw_dark_filename

    # Save the ASN
    with open("test_asn.json", "w") as out_asn:
        json.dump(asn, out_asn)

    # Create and call the pipeline object
    liger_iris_pipeline.ProcessImagerL2Pipeline.call("test_asn.json", config_file="liger_iris_pipeline/tests/data/image2_iris.cfg")

    # Download the sky background???
    #ref_filename = get_data_from_url("17905553")

    # Test the local output file with the reference file
    with liger_iris_pipeline.datamodels.LigerIRISImageModel('test_iris_subtract_bg_flat_cal.fits') as out, \
        liger_iris_pipeline.datamodels.LigerIRISImageModel(raw_background_filename) as ref:
        np.testing.assert_allclose(out.data, ref.data, rtol=1e-6)

def test_image2_subarray(tmp_path):
    with open("liger_iris_pipeline/tests/data/asn_subtract_bg_flat.json") as fp:
        asn = load_asn(fp)
    raw_science_filename = get_data_from_url("48191524")
    input_model = liger_iris_pipeline.datamodels.LigerIRISImageModel(raw_science_filename)

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

    raw_dark_filename = get_data_from_url("48191518")
    raw_background_filename = '/Users/cale/Desktop/IRIS_Test_Data/test_iris_subtract_bg_flat_cal.fits'
    asn["products"][0]["members"][0]["expname"] = str(raw_science_subarray_filename)
    asn["products"][0]["members"][1]["expname"] = raw_background_filename
    with open("test_asn.json", "w") as out_asn:
        json.dump(asn, out_asn)
    liger_iris_pipeline.pipeline.ProcessImagerL2Pipeline.call("test_asn.json", config_file="iris_pipeline/tests/data/image2_iris.cfg")
    ref_filename = get_data_from_url("17905553")
    with liger_iris_pipeline.datamodels.LigerIRISImageModel("test_iris_subtract_bg_flat_cal.fits") as out, \
        liger_iris_pipeline.datamodels.LigerIRISImageModel(ref_filename) as ref:
        np.testing.assert_allclose(out.data, ref.data[subarray_slice], rtol=1e-6)

