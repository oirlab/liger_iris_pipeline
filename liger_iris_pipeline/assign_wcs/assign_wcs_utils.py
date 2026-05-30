import logging
#from astropy.modeling import models
#from astropy import coordinates as coord
#from astropy import units as u
#from gwcs import coordinate_frames as cf
#from gwcs import WCS

from liger_iris_pipeline import datamodels

from astropy.wcs import WCS

logger = logging.getLogger(__name__)

__all__ = ["load_wcs_imager"]


def load_wcs_imager(input_model : datamodels.ImagerModel, reference_files : dict):
    """
    Create a gWCS object and store it in ``input_model.meta``.

    Parameters
    ----------
    input_model : ImagerModel
        The exposure to assign wcs to.
    reference_files : dict
        A dict {reftype: reference_file_name} containing all
        reference files that apply to this exposure.
    """
    # output_model = input_model.copy()
    # shift_by_crpix = models.Shift(
    #     -(input_model.meta.wcsinfo.crpix1) * u.pix # Removed -1
    # ) & models.Shift(-(input_model.meta.wcsinfo.crpix2) * u.pix) # Removed -1
    # pix2sky = getattr(
    #     models, "Pix2Sky_{}".format(input_model.meta.wcsinfo.ctype1[-3:])
    # )()
    # celestial_rotation = models.RotateNative2Celestial(
    #     input_model.meta.wcsinfo.crval1 * u.deg,
    #     input_model.meta.wcsinfo.crval2 * u.deg,
    #     180 * u.deg,
    # )
    # pix2sky.input_units_equivalencies = {
    #     "x": u.pixel_scale(input_model.meta.wcsinfo.cdelt1 * u.deg / u.pix),
    #     "y": u.pixel_scale(input_model.meta.wcsinfo.cdelt2 * u.deg / u.pix),
    # }
    # det2sky = shift_by_crpix | pix2sky | celestial_rotation
    # det2sky.name = "linear_transform"
    # detector_frame = cf.Frame2D(
    #     name="detector", axes_names=("x", "y"), unit=(u.pix, u.pix)
    # )
    # sky_frame = cf.CelestialFrame(
    #     reference_frame=getattr(
    #         coord, input_model.meta.coordinates.reference_frame
    #     )(),
    #     name="sky_frame",
    #     unit=(u.deg, u.deg),
    # )
    # pipeline = [(detector_frame, det2sky), (sky_frame, None)]

    # wcs = WCS(pipeline)

    assert isinstance(input_model, datamodels.ImagerModel)

    wcsinfo = input_model.meta.wcsinfo

    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [wcsinfo.crpix1, wcsinfo.crpix2]
    wcs.wcs.crval = [wcsinfo.crval1, wcsinfo.crval2]
    wcs.wcs.cdelt = [wcsinfo.cdelt1, wcsinfo.cdelt2]
    wcs.wcs.ctype = [wcsinfo.ctype1, wcsinfo.ctype2]
    wcs.wcs.cunit = [wcsinfo.cunit1, wcsinfo.cunit2]

    output_model = input_model.copy()
    #output_model.wcs = wcs
    output_model.meta.wcs = wcs
    #output_model.wcs = wcs

    return output_model
