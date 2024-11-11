# Imports
import liger_iris_pipeline

liger_iris_pipeline.monkeypatch_jwst_datamodels()
import numpy as np

# See README.md for notes on testing data
from liger_iris_pipeline.tests.test_utils import get_data_from_url

from jwst import datamodels
from liger_iris_pipeline.assign_wcs.assign_wcs import load_wcs
import astropy.units as u
from astropy import wcs
from astropy.tests.helper import assert_quantity_allclose


def test_assign_wcs_step():
    # Grab simulated raw frame
    raw_science_filename = get_data_from_url("48191524")
    input_model = datamodels.open(raw_science_filename)

    # Ensure we haven't already performed the correction.
    # NOTE: Instead check for result.meta.cal_step.assign_wcs == "SKIPPED" vs. "COMPLETE"?
    assert not hasattr(input_model.meta, "wcs")

    # Add manual WCS info for now
    input_model.meta.wcsinfo.ctype1 = "RA---TAN"
    input_model.meta.wcsinfo.ctype2 = "DEC--TAN"
    input_model.meta.wcsinfo.cdelt1 = 1e-6
    input_model.meta.wcsinfo.cdelt2 = 1e-6
    input_model.meta.wcsinfo.crval1 = 265
    input_model.meta.wcsinfo.crval2 = -29
    input_model.meta.wcsinfo.crpix1 = 2048.12
    input_model.meta.wcsinfo.crpix2 = 2048.12

    # Assign WCS for now just parses the `wcsinfo` metadata assigned above and creates a
    # `gwcs.WCS` instance with the proper coordinate transformations using `astropy.modeling`.
    step = liger_iris_pipeline.AssignWcsStep()
    output_model = step.run(input_model)

    # Test
    assert_quantity_allclose(
        (
            input_model.meta.wcsinfo.crval1 * u.deg,
            input_model.meta.wcsinfo.crval2 * u.deg,
        ),
        output_model.meta.wcs(
            input_model.meta.wcsinfo.crpix1 * u.pix,
            input_model.meta.wcsinfo.crpix2 * u.pix,
        ),
    )

    # Now test against astropy's WCS
    input_model.to_fits("temp_wcs.fits", overwrite=True)
    astropy_fits_wcs = wcs.WCS("temp_wcs.fits")
    astropy_fits_wcs.pixel_to_world_values(0, 0)
    output_model.meta.wcs(0 * u.pix, 0 * u.pix)
    pixels = [0, 4096] * u.pix

    for pix_x in pixels:
        for pix_y in pixels:
            assert_quantity_allclose(
                astropy_fits_wcs.pixel_to_world_values(pix_x, pix_y) * u.deg,
                output_model.meta.wcs(pix_x, pix_y),
            )
