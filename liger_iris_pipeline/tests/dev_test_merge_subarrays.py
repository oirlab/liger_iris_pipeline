# TODO: UPDATE THIS TEST
# # Imports
# from liger_iris_pipeline import MergeSubarraysStep
# import numpy as np
# import json


# def test_merge_subarrays(tmp_path):

#     reduced_science_frame_filename = '/Users/cale/Desktop/IRIS_Test_Data/reduced_science_frame_sci_with_subarrays_20240831.fits'
#     reduced_subarray1_filename = '/Users/cale/Desktop/IRIS_Test_Data/reduced_science_frame_sci_subarray_1_20240831.fits'
#     reduced_subarray2_filename = '/Users/cale/Desktop/IRIS_Test_Data/reduced_science_frame_sci_subarray_2_20240831.fits'

#     # Create an ASN for this test
#     asn = {
#         "asn_rule": "Asn_Image",
#         "asn_pool": "pool",
#         "asn_type": "image3",
#         "products": [
#             {
#                 "name": "test_merge_subarrays_asn",
#                 "members": [
#                     {
#                         "expname": reduced_science_frame_filename,
#                         "exptype": "science"
#                     },
#                     {
#                         "expname": reduced_subarray1_filename,
#                         "exptype": "science"
#                     },
#                     {
#                         "expname": reduced_subarray2_filename,
#                         "exptype": "science"
#                     }
#                 ]
#             }
#         ]
#     }

#     # Save to file
#     asn_temp_filename = tmp_path / "test_asn.json"
#     with open(asn_temp_filename, "w+") as f:
#         json.dump(asn, f)

#     # Run the merge subarray pipeline
#     result = MergeSubarraysStep().call(asn_temp_filename)

#     # Check that the image is valid
#     assert np.all(np.logical_not(np.isnan(result.data)))