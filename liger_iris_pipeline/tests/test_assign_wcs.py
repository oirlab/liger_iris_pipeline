from liger_iris_pipeline import datamodels, AssignWCSStep

import astropy.units as u
from astropy import wcs
from astropy.tests.helper import assert_quantity_allclose
from liger_iris_pipeline.tests.utils import download_osf_file


def test_assign_wcs_step(tmp_path):

    # Grab simulated raw frame
    remote_sci_L1_filename = 'IRIS/L1/2024B-P123-008_IRIS_IMG1_SCI-J1458+1013-Y-4.0_LVL1_0001-00.fits'
    sci_L1_filename = download_osf_file(remote_sci_L1_filename, use_cached=True)
    input_model = datamodels.open(sci_L1_filename)

    # Ensure we haven't already performed the correction.
    # NOTE: Instead check for result.meta.cal_step.assign_wcs == "SKIPPED" vs. "COMPLETE"?
    assert not hasattr(input_model.meta, "wcs")

    # Assign WCS for now just parses the `wcsinfo` metadata assigned above and creates a
    # `gwcs.WCS` instance with the proper coordinate transformations using `astropy.modeling`.
    step = AssignWCSStep()
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
    filename_wcs = str(tmp_path / "temp_wcs.fits")
    input_model.to_fits(filename_wcs, overwrite=True)
    # warning: FITSFixedWarning: RADECSYS= 'ICRS ' / Name of the coordinate
    # reference frame the RADECSYS keyword is deprecated, use RADESYSa.
    astropy_fits_wcs = wcs.WCS(filename_wcs)
    pixels = [0, 4095] * u.pix

    for pix_x in pixels:
        for pix_y in pixels:
            assert_quantity_allclose(
                astropy_fits_wcs.pixel_to_world_values(pix_x - 1*u.pix, pix_y - 1*u.pix) * u.deg, # NOTE: Why -1 required?
                #astropy_fits_wcs.pixel_to_world_values(pix_x, pix_y) * u.deg,
                output_model.meta.wcs(pix_x, pix_y),
            )