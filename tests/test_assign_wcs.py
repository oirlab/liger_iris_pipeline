from liger_iris_pipeline import datamodels
from liger_iris_pipeline.assign_wcs import AssignWCSStep
import numpy as np
from numpy.testing import assert_allclose

import astropy.units as u
from astropy import wcs
from astropy.tests.helper import assert_quantity_allclose

#### NOTE ####
#### The purpose of this test is to test more complex methods of WCS assignment.
##############

def test_assign_wcs_step(tmp_path):

    # Input L1 model
    sci_model_L1 = datamodels.ImagerModel(
        data=np.ones((2048, 2048)),
        meta={
            'exposure.mjd_start' : 60577.0,
            'instrument.mode' : 'IMG',
            'target.ra': 0.0,
            'target.dec': 0.0,
            'instrument.scale' : 0.01,
        },
    )

    assert not hasattr(sci_model_L1.meta, "wcs")

    output_model = AssignWCSStep.call(sci_model_L1)

    # Test zero points are converted correctly
    ra1 = sci_model_L1.meta.wcsinfo.crval1
    dec1 = sci_model_L1.meta.wcsinfo.crval2

    ra2, dec2 = output_model.meta.wcs.all_pix2world(
        sci_model_L1.meta.wcsinfo.crpix1,
        sci_model_L1.meta.wcsinfo.crpix2,
        1,  # origin=1 tells astropy the inputs are 1-based FITS pixel coordinates
    )

    ra1 = ra1 % 360
    ra2 = ra2 % 360

    assert_allclose((ra1, dec1), (ra2, dec2), atol=1E-10)

    # NOTE: Internally we are using wcs until gwcs is sorted out
    # This effectively tests the ongoing implementation in ``load_wcs_imager``
    # against astropy's WCS, which is still a good check.
    filename_wcs = str(tmp_path / "temp_wcs.fits")
    sci_model_L1.save(filename_wcs)
    astropy_fits_wcs = wcs.WCS(filename_wcs)
    
    pixels_y = [1, sci_model_L1.data.shape[0] // 2, sci_model_L1.data.shape[0]] * u.pix
    pixels_x = [1, sci_model_L1.data.shape[1] // 2, sci_model_L1.data.shape[1]] * u.pix

    for pix_x in pixels_x:
        for pix_y in pixels_y:
            v1 = output_model.meta.wcs.pixel_to_world_values(pix_x, pix_y) * u.deg
            v2 = astropy_fits_wcs.pixel_to_world_values(pix_x, pix_y) * u.deg
            assert_quantity_allclose(v1, v2)