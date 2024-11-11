# Imports
import liger_iris_pipeline
liger_iris_pipeline.monkeypatch_jwst_datamodels()
import numpy as np

# See README.md for notes on testing data
from liger_iris_pipeline.tests.test_utils import get_data_from_url

import json
from jwst.associations import load_asn

def test_image2(tmp_path):

    # Load the association file
    # Contains a science and sky exposure to process
    with open("liger_iris_pipeline/tests/data/asn_subtract_bg_flat.json") as fp:
        asn = load_asn(fp)

    # Download the raw science frame
    raw_science_filename = get_data_from_url("48191524")

    # Download sky background frame
    background_filename = get_data_from_url("48903439")

    # Compare L2 output below to this file
    ref_filename = get_data_from_url("48737014")

    # Overwrite the ASN with these files
    asn["products"][0]["members"][0]["expname"] = raw_science_filename
    asn["products"][0]["members"][1]["expname"] = background_filename

    # Save the modified ASN
    asn_temp_filename = tmp_path / "test_asn.json"
    with open(asn_temp_filename, "w") as f:
        json.dump(asn, f)

    # Create and call the pipeline object
    # Pipeline saves L2 file: test_iris_imageL2_cal.fits
    liger_iris_pipeline.ProcessImagerL2Pipeline.call(asn_temp_filename, config_file="liger_iris_pipeline/tests/data/image2_iris.cfg")

    # Compare the output file we just created with an established result
    with liger_iris_pipeline.datamodels.LigerIrisImageModel('test_iris_subtract_bg_flat_cal.fits') as out, \
        liger_iris_pipeline.datamodels.LigerIrisImageModel(ref_filename) as ref:
        np.testing.assert_allclose(out.data, ref.data, rtol=1e-6)

def test_image2_subarray(tmp_path):
    
    # Load the association
    with open("liger_iris_pipeline/tests/data/asn_subtract_bg_flat.json") as f:
        asn = load_asn(f)

    # Download the raw science frame
    raw_science_filename = get_data_from_url("48191524")
    input_model = liger_iris_pipeline.datamodels.LigerIrisImageModel(raw_science_filename)

    # Subarray params
    xstart = 100
    ystart = 200
    xsize = 50
    ysize = 60
    input_model.meta.subarray.name = "CUSTOM"
    input_model.meta.subarray.xstart = xstart + 1
    input_model.meta.subarray.ystart = ystart + 1
    input_model.meta.subarray.xsize = xsize
    input_model.meta.subarray.ysize = ysize

    # Subarray indices
    subarray_slice = np.s_[ystart:ystart+ysize, xstart:xstart+xsize]

    # Slice the data
    # NOTE: .err must be first since it's not in the FITS file and is created on the fly when accessed
    input_model.err = np.array(input_model.err[subarray_slice])
    input_model.data = np.array(input_model.data[subarray_slice])
    input_model.dq = np.array(input_model.dq[subarray_slice])

    # Save the subarray science frame
    raw_science_subarray_filename = tmp_path / "temp_subarray_science.fits"
    input_model.write(raw_science_subarray_filename)

    # Download sky background frame
    background_filename = get_data_from_url("48903439")

    # Store in ASN
    asn["products"][0]["members"][0]["expname"] = str(raw_science_subarray_filename)
    asn["products"][0]["members"][1]["expname"] = background_filename

    # Save the modified ASN
    asn_temp_filename = tmp_path / "test_asn.json"
    with open(asn_temp_filename, "w") as f:
        json.dump(asn, f)

    # Call pipeline with test ASN
    liger_iris_pipeline.pipeline.ProcessImagerL2Pipeline.call(asn_temp_filename, config_file="liger_iris_pipeline/tests/data/image2_iris.cfg")

    # Compare L2 output below to this file
    ref_filename = get_data_from_url("48737014")

    # Test the local output file with the reference file
    with liger_iris_pipeline.datamodels.LigerIrisImageModel("test_iris_subtract_bg_flat_cal.fits") as out, \
        liger_iris_pipeline.datamodels.LigerIrisImageModel(ref_filename) as ref:
        np.testing.assert_allclose(out.data, ref.data[subarray_slice], rtol=1e-6)