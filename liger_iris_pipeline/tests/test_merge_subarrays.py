# TODO: UPDATE THIS TEST
# # Imports
from liger_iris_pipeline import MergeSubarraysStep
from liger_iris_pipeline.associations import L1Association
import numpy as np
import json



# This test works locally, but these files are not stored in the Liger_IRIS_Test_Data repo until the 
# "Embedding ASDF in FITS" is better understood
# def test_merge_subarrays(tmp_path):

#     reduced_science_frame_filename = '/Users/cale/Desktop/Liger_IRIS_Test_Data_OLD/reduced_science_frame_sci_with_subarrays_20240831.fits'
#     reduced_subarray1_filename = '/Users/cale/Desktop/Liger_IRIS_Test_Data_OLD/reduced_science_frame_sci_subarray_1_20240831.fits'
#     reduced_subarray2_filename = '/Users/cale/Desktop/Liger_IRIS_Test_Data_OLD/reduced_science_frame_sci_subarray_2_20240831.fits'

#     # ASN
#     asn = L1Association.from_product({
#         "members": [
#             {
#                 "expname": reduced_science_frame_filename,
#                 "exptype": "SCI",
#             },
#             {
#                 "expname": reduced_subarray1_filename,
#                 "exptype": "SCI"
#             },
#             {
#                 "expname": reduced_subarray2_filename,
#                 "exptype": "SCI"
#             }
#         ]
#     })

#     # Run the merge subarray step
#     result = MergeSubarraysStep().run(asn)

#     # Check that the image is valid
#     assert np.all(np.logical_not(np.isnan(result.data)))