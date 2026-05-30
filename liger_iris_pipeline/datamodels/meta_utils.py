from astropy.time import Time
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, ICRS
import astropy.units as u
import numpy as np

_KECK = EarthLocation.of_site('Keck Observatory')


def set_default_imager_wcs_meta(model):
    if (
        model.meta.target.ra is None
        or model.meta.target.dec is None
        or model.meta.instrument.scale is None
        or model.shape is None
        ):
        return model
    
    ny, nx = model.shape
    scale_deg = model.meta.instrument.scale / 3600.0

    model.meta.wcsinfo.crpix1 = (nx + 1) / 2
    model.meta.wcsinfo.crpix2 = (ny + 1) / 2

    model.meta.wcsinfo.crval1 = model.meta.target.ra
    model.meta.wcsinfo.crval2 = model.meta.target.dec

    model.meta.wcsinfo.ctype1 = 'RA---TAN'
    model.meta.wcsinfo.ctype2 = 'DEC--TAN'

    model.meta.wcsinfo.cunit1 = 'deg'
    model.meta.wcsinfo.cunit2 = 'deg'

    model.meta.wcsinfo.cdelt1 = -scale_deg
    model.meta.wcsinfo.cdelt2 =  scale_deg

    return model

def set_default_ifs_wcs_meta(model):
    if (
        model.meta.target.ra is None
        or model.meta.target.dec is None
        or model.meta.instrument.scale is None
        or model.shape is None
        or model.wave is None
        ):
        return model
    ny, nx = model.shape

    scale_deg = model.meta.instrument.scale / 3600.0

    model.meta.wcsinfo.crpix1 = (nx + 1) / 2
    model.meta.wcsinfo.crpix2 = (ny + 1) / 2
    model.meta.wcsinfo.crpix3 = 1

    model.meta.wcsinfo.crval1 = model.meta.target.ra
    model.meta.wcsinfo.crval2 = model.meta.target.dec
    model.meta.wcsinfo.crval3 = model.wave[0]

    model.meta.wcsinfo.ctype1 = 'RA---TAN'
    model.meta.wcsinfo.ctype2 = 'DEC--TAN'
    model.meta.wcsinfo.ctype3 = 'WAVE'

    model.meta.wcsinfo.cunit1 = 'deg'
    model.meta.wcsinfo.cunit2 = 'deg'
    model.meta.wcsinfo.cunit3 = 'micron'

    model.meta.wcsinfo.cdelt1 = -scale_deg
    model.meta.wcsinfo.cdelt2 = scale_deg
    model.meta.wcsinfo.cdelt3 = model.wave[1] - model.wave[0]
    
    return model

def set_default_exposure_meta(model):
    if model.meta.exposure.exposure_time is None:
        model.meta.exposure.exposure_time = 0.0
    if model.meta.exposure.mjd_start is None and model.meta.datetime_obs is not None:
        model.meta.exposure.mjd_start = Time(model.meta.datetime_obs, format='isot').mjd
    if model.meta.exposure.mjd_end is None:
        model.meta.exposure.mjd_end = model.meta.exposure.mjd_start + model.meta.exposure.exposure_time / 86400
    if model.meta.exposure.type is None:
        if not hasattr(model, '_ref_type'):
            model.meta.exposure.type = 'SCI'
    if model.meta.exposure.nframes is None:
       model.meta.exposure.nframes = 1
    if model.meta.exposure.exposure_number is None:
        model.meta.exposure.exposure_number = 1
    if model.meta.exposure.read_mode is None:
        model.meta.exposure.read_mode = 'DEFAULT'
    return model

def get_semester_id(date_time : str) -> str:
    """
    Get the semester ID for a date time string.

    Parameters
    ----------
    date_time : str
        The date time string in ISO format.

    Returns
    -------
    str
        The semester ID.

    Notes
    _____
    This method is for development purposes only.
    In practice, semester IDs will be populated from the metadata.
    """
    t = Time(date_time, format='isot', scale='utc')
    year = t.datetime.year
    month = t.datetime.month
    day = t.datetime.day
    sem = 'A' if (month < 8 or (month == 8 and day < 1)) else 'B'
    return f"{year}{sem}"

def set_default_target_meta(model):

    # Starting Azimuth, Elevation, RA, Dec
    if model.meta.target.ra is None and model.meta.target.elevation_start is not None and model.meta.exposure.mjd_start is not None:
        coord_start = AltAz(
            alt=model.meta.target.elevation_start * u.deg,
            az=model.meta.target.azimuth_start * u.deg,
            obstime=Time(model.meta.exposure.mjd_start, format='mjd'),
            location=_KECK
        ).transform_to(ICRS())
        model.meta.target.ra = coord_start.ra.deg
        model.meta.target.dec = coord_start.dec.deg
    else:
        model.meta.target.elevation_start = 90.0
        model.meta.target.azimuth_start = 0.0
        coord_start = AltAz(
            alt=model.meta.target.elevation_start * u.deg,
            az=model.meta.target.azimuth_start * u.deg,
            obstime=Time(model.meta.exposure.mjd_start, format='mjd'),
            location=_KECK
        ).transform_to(ICRS())
        model.meta.target.ra = coord_start.ra.deg
        model.meta.target.dec = coord_start.dec.deg

    # Ending Azimuth, Elevation
    if model.meta.target.elevation_end is None:
       coord_end = SkyCoord(
            ra=model.meta.target.ra * u.deg,
            dec=model.meta.target.dec * u.deg
        ).transform_to(AltAz(
            obstime=Time(model.meta.exposure.mjd_end, format='mjd'),
            location=_KECK)
       )
       model.meta.target.elevation_end = coord_end.alt.deg
       model.meta.target.azimuth_end = coord_end.az.deg
    return model

def set_full_subarray_meta(model):
    if model.shape is not None:
        if model.meta.subarray.id is None and model.meta.subarray.name is None:
            model.meta.subarray.name = 'FULL'
            model.meta.subarray.id = 0
        if model.meta.subarray.ystart is None:
            model.meta.subarray.ystart = 1
        if model.meta.subarray.xstart is None:
            model.meta.subarray.xstart = 1
        model.meta.subarray.ysize = model.shape[0]
        model.meta.subarray.xsize = model.shape[1]
        model.meta.subarray.detxsize = 2048 if model.meta.instrument.name == 'Liger' else 4096
        model.meta.subarray.detysize = 2048 if model.meta.instrument.name == 'Liger' else 4096
        model.meta.subarray.fastaxis = 0
        model.meta.subarray.slowaxis = 1
    return model

def update_model_meta(model, **kwargs):
    for key, value in kwargs.items():
        attrs = key.split(".")

        # Allow optional leading "meta"
        if attrs and attrs[0] == "meta":
            attrs = attrs[1:]

        target = model.meta

        for attr in attrs[:-1]:
            if hasattr(target, attr):
                target = getattr(target, attr)
            else:
                target = None
                break

        if target is not None:
            setattr(target, attrs[-1], value)