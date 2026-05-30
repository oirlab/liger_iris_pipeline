import numpy as np
from astropy.coordinates import HADec, AltAz, EarthLocation

__all__ = ['calc_parallactic_angle', 'KECK_LOCATION']

KECK_LOCATION = EarthLocation.of_site('Keck Observatory')

def calc_parallactic_angle(altaz_coord: AltAz, location : EarthLocation) -> float:
    """
    Calculate the parallactic angle for a given AltAz coordinate and Earth location.

    Parameters
    ----------
    altaz_coord : AltAz
        The astropy AltAz coordinate of the object.
    location : EarthLocation | None
        The astropy Earth location of the observer.
        Defaults to Keck Observatory if None is provided.

    Returns
    -------
    P_deg : float
        The parallactic angle in degrees.
    """
    if location is None:
        location = KECK_LOCATION
    assert isinstance(location, EarthLocation), "location must be an astropy EarthLocation"
    hadec = altaz_coord.transform_to(HADec(obstime=altaz_coord.obstime, location=location))
    H = hadec.ha.rad
    delta = hadec.dec.rad
    phi = location.lat.rad
    num = np.sin(H) * np.cos(phi)
    den = np.sin(phi) * np.cos(delta) - np.sin(delta) * np.cos(phi) * np.cos(H)
    if np.isclose(den, 0.0, atol=1e-12):
        return 0.0
    P = np.arctan2(num, den)
    P_deg = np.degrees(P)
    return P_deg