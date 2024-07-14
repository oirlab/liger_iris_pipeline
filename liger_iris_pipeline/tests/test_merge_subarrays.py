# Imports
import liger_iris_pipeline
liger_iris_pipeline.monkeypatch_jwst_datamodels()
from liger_iris_pipeline import MergeSubarraysStep
from liger_iris_pipeline.tests.test_utils import get_data_from_url
import numpy as np
import json
from jwst import datamodels

def test_merge_subarrays():

    # file asn_merge_subarrays.json
    # ASN = Association table for an observation set
    asn_json = {
        "asn_rule": "Asn_Image",
        "asn_pool": "pool",
        "asn_type": "image3",
        "products": [
            {
                "name": "test_merge_subarrays_asn",
                "members": [
                    {
                        "expname": "data/reduced_science_frame_sci_with_subarrays.fits",
                        "exptype": "science"
                    },
                    {
                        "expname": "data/reduced_science_frame_sci_subarray_1.fits",
                        "exptype": "science"
                    },
                    {
                        "expname": "data/reduced_science_frame_sci_subarray_2.fits",
                        "exptype": "science"
                    }
                ]
            }
        ]
    }

    # Save to JSON
    with open("temp_asn_merge_subarrays.json", "w+") as f:
        json.dump(asn_json, f)

    # Create step
    step = MergeSubarraysStep()
    image = step.run("temp_asn_merge_subarrays.json")

    # Load individual subarray images we want to merge.
    #image_with_subarrays_filename = get_data_from_url("11953512")
    #original_model = datamodels.open("data/reduced_science_frame_sci_with_subarrays.fits")

    # Test
    assert np.all(np.logical_not(np.isnan(image.data)))

test_merge_subarrays()