# Imports
import liger_iris_pipeline
liger_iris_pipeline.monkeypatch_jwst_datamodels()
import numpy as np

import json

# See README.md for notes on testing data
from liger_iris_pipeline.tests.test_utils import get_data_from_url


def test_merge_subarrays(tmp_path):

    # Download the test data
    reduced_science_frame_filename = get_data_from_url("48911932")
    reduced_subarray1_filename = get_data_from_url("48911917")
    reduced_subarray2_filename = get_data_from_url("48911914")

    # Create an ASN for this test
    asn = {
        "asn_rule": "Asn_Image",
        "asn_pool": "pool",
        "asn_type": "image3",
        "products": [
            {
                "name": "test_merge_subarrays_asn",
                "members": [
                    {
                        "expname": reduced_science_frame_filename,
                        "exptype": "science"
                    },
                    {
                        "expname": reduced_subarray1_filename,
                        "exptype": "science"
                    },
                    {
                        "expname": reduced_subarray2_filename,
                        "exptype": "science"
                    }
                ]
            }
        ]
    }

    # Save to file
    asn_temp_filename = tmp_path / "test_asn.json"
    with open(asn_temp_filename, "w+") as f:
        json.dump(asn, f)

    # Run the merge subarray pipeline
    result = liger_iris_pipeline.MergeSubarraysStep().call(asn_temp_filename)

    # Check that the image is valid
    assert np.all(np.logical_not(np.isnan(result.data)))