from astropy.coordinates import EarthLocation, SkyCoord, AltAz, SkyOffsetFrame
import numpy as np
from astropy.time import Time
from astropy.table import Table
import astropy.units as u

from . import slalib
from ..utils.sky_utils import calc_parallactic_angle

import os
import urllib.request
from astropy.utils.data import _get_download_cache_loc

KECK_LOCATION = EarthLocation.of_site('Keck Observatory')


def calc_dar_coeffs(
    location : EarthLocation,
    wave : float, # microns
    temperature : float = 273.0,  # K
    pressure : float = 615.0, # hPa
    humidity: float = 0.2, # frac
    tlr : float = 0.0065,
    eps : float = 1E-9
) -> tuple[float, float]:
    """
    Calculate refraction coefficients using SLALIB.

    Parameters
    ----------
    location : EarthLocation
        astropy observatory location.
    wave : float
        Wavelength in microns.
    temp : float, optional
        Temperature in Kelvin. Default is 273.0.
    pressure : float, optional
        Pressure in hPa. Default is 615.0.
    humidity : float, optional
        Humidity fraction. Default is 0.2.
    tlr : float, optional
        Temperature lapse rate. Default is 0.0065.
    eps : float, optional
        Small epsilon value for convergence. Default is 1E-9.

    Returns
    -------
    A : float
        Linear (in tanZ) refraction coefficient.
    B : float
        Cubic (in tanZ) refraction coefficient.
    """
    latitude = location.lat.deg
    height = location.height.to_value('m')
    A, B = slalib.refco(
        HM=height,
        TDK=temperature,
        PMB=pressure, 
        RH=humidity,
        WL=wave,
        PHI=latitude,
        TLR=tlr,
        EPS=eps
    )
    return A, B


def calc_dar_shifts(
    location : EarthLocation,
    altaz_coord : AltAz,
    size : tuple[int, int],
    scale : float,
    wave : float,
    rotation : float = 0.0,
    temperature : float = 273.0,
    pressure : float = 615.0,
    humidity : float = 0.3,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculate DAR shifts in pixels.

    Parameters
    ----------
    wave : float
        Wavelength in microns.
    scale : float
        Plate scale in arcsec/pixel.
    size : tuple[int, int]
        Size of the detector in pixels (ny, nx).
    rotation : float
        Instrument rotation in degrees relative to the parallactic angle.
    temperature : float
        Temperature in Kelvin.
    pressure : float
        Pressure in hPa.
    humidity : float
        Humidity fraction. Defaults to 0.3 (30%).

    Returns
    -------
    dy : np.ndarray
        Y shifts in pixels.
    dx : np.ndarray
        X shifts in pixels.
    """
    
    # Get refraction coefficients
    # dZ = A tanZ + B tanZ^3
    A, B = calc_dar_coeffs(location, wave, temperature, pressure, humidity)

    # Altitude of observation
    altitude = altaz_coord.alt.deg

    # Calculate the parallactic angle
    parallactic_angle = calc_parallactic_angle(location, altaz_coord)
    
    # Calculate zenith angle effects
    Z = 90 - altitude
    tanZ = np.tan(np.radians(Z))
    tmp = 1 + tanZ**2
    
    # Linear and quadratic terms
    L = tmp * (A + 3 * B * tanZ**2) # Unitless
    Q = -tmp * (A * tanZ + 3 * B * (tanZ + 2 * tanZ**3)) # Radians^-1
    Q *= 1 / 206265 # Convert Q to arcsec^-1
    Q *= 1 / scale # Convert Q to pixels^-1
    
    # Create grid of pixel coords with origin at center
    axisX = np.arange(size[0]) - size[0] / 2
    axisY = np.arange(size[1]) - size[1] / 2
    Y, X = np.meshgrid(axisY, axisX, indexing='ij')
    
    # Rotate CW to parallactic angle frame, need to account for instrument rotation
    PA_eff = np.radians(parallactic_angle + rotation)
    sina, cosa = np.sin(PA_eff), np.cos(PA_eff)
    
    # Rotate CW to align such that to zenith is along +Y
    X_rot = X * cosa + Y * sina
    Y_rot = -X * sina + Y * cosa

    # Apply DAR transformation to Y component
    Y_rot = Y_rot * (1 + L) + Y_rot * np.abs(Y_rot) * Q

    # Rotate CCW back to original frame
    X2 = X_rot * cosa - Y_rot * sina
    Y2 = X_rot * sina + Y_rot * cosa

    # Calculate displacements
    DX = X2 - X
    DY = Y2 - Y

    return DY, DX


def get_koa_weather_data(date_time : Time, use_cached : bool = True) -> dict[str, float]:
    """
    Get KOA weather data for a given observation time.

    Parameters
    ----------
    obs_time : astropy.time.Time
        Time of observation in local time.

    Returns
    -------
    dict[str, float]
        Dictionary with keys:
        - temperature : float
            Atmospheric temperature in Kelvin.
        - humidity : float
            Atmospheric humidity as a fraction.
        - pressure : float
            Atmospheric pressure in hPa.
    """

    # Download each param (or cached)
    filepath_temp = download_koa_dat_files(date_time, parameter='OutsideTemp', use_cached=use_cached)
    filepath_hum = download_koa_dat_files(date_time, parameter='OutsideHumidity', use_cached=use_cached)
    filepath_pres = download_koa_dat_files(date_time, parameter='Pressure', use_cached=use_cached)

    # Get each param using closest in time
    # NOTE: Consider interpolating, look at timestamps once downloading from KOA works
    temp_table = Table.read(
        filepath_temp,
        format='ascii.basic',
        data_start=1,
        delimiter='\t',
        guess=False,
        fast_reader=False,
        header_start=None,
        names=['row', 'temp', 'timeinsecs', 'datetime_utc']
    )
    temp_datetimes = Time(temp_table['datetime_utc'], format='iso').datetime
    temp_idx = np.argmin(np.abs(temp_datetimes - date_time.datetime))
    atm_temp = temp_table[temp_idx]['temp'] + 273.15 # C to K # NOTE: KAI uses 272.15?

    # Humidity
    hum_table = Table.read(
        filepath_hum,
        format='ascii.basic',
        data_start=1,
        delimiter='\t',
        guess=False,
        fast_reader=False,
        header_start=None,
        names=['row', 'humidity', 'timeinsecs', 'datetime_utc']
    )
    hum_datetimes = Time(hum_table['datetime_utc'], format='iso').datetime
    hum_idx = np.argmin(np.abs(hum_datetimes - date_time.datetime))
    atm_hum = hum_table[hum_idx]['humidity'] / 100.0

    # Pressure
    pres_table = Table.read(
        filepath_pres,
        format='ascii.basic',
        data_start=1,
        delimiter='\t',
        guess=False,
        fast_reader=False,
        header_start=None,
        names=['row', 'pressure', 'timeinsecs', 'datetime_utc']
    )
    pres_datetimes = Time(pres_table['datetime_utc'], format='iso').datetime
    pres_idx = np.argmin(np.abs(pres_datetimes - date_time.datetime))
    atm_pres = pres_table[pres_idx]['pressure']

    return dict(temperature=atm_temp, humidity=atm_hum, pressure=atm_pres)


def download_koa_dat_files(
    date_time : Time,
    parameter : str,
    telescope : str = 'k1',
    output_dir : str | None = None,
    use_cached : bool = True
) -> str:
    """
    Download KOA weather data files for a given date and parameter.

    Parameters
    ----------
    date_time : astropy.time.Time
        Date time of the observation.
    parameter : str
        Parameter name to download (e.g., 'OutsideTemp', 'OutsideHumidity', 'Pressure').
    telescope : str
        Telescope identifier ('k1' for Keck I, 'k2' for Keck II). Default is 'k1'.
    output_dir : str | None
        Directory to save the downloaded file. Default is ~/.astropy/cache/koa_weather/<filename.dat>.
    use_cached : bool
        Whether to use cached file if it exists. Default is True.

    Returns
    -------
    output_path : str
        Path to the downloaded file.
    """

    # Format date string
    date_str = f"{date_time.datetime.year}{date_time.datetime.month:02d}{date_time.datetime.day:02d}"

    # Get output path
    if output_dir is None:
        output_dir = os.path.abspath(_get_download_cache_loc()) + os.sep + 'koa_weather'
    else:
        output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'{telescope}_{date_str}_{parameter}.dat')

    # Check cache
    if use_cached and os.path.isfile(output_path):
        return output_path

    # URL to KOA weather
    url = f'https://koa.ipac.caltech.edu/data33/WEATHER/{date_str}/nightly2/{telescope}_{date_str}_{parameter}.dat'
    print(f'Downloading KOA weather data from {url} ...')

    # Get KOA weather data
    with urllib.request.urlopen(url) as response:
        atm_data = response.read()

    # Download file
    mode = 'wb' if isinstance(atm_data, bytes) else 'w'
    with open(output_path, mode) as f:
        f.write(atm_data)

    # Return output path
    return output_path
