from ..stpipe.base_step import LigerIRISStep
from .dar import calc_dar_shifts, get_koa_weather_data
from .. import datamodels
import numpy as np
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time
import astropy.units as u

from ..calibrations import DistortionSelector
from ..utils.subarray import get_subarray_model
from .resample import resample_distortion_drizzle

import logging
logger = logging.getLogger(__name__)


__all__ = ["DistortionCorrectionStep"]

KECK_LOCATION = EarthLocation.of_site('Keck Observatory')


class DistortionCorrectionStep(LigerIRISStep):
    """
    This step does one or both of the following corrections on the input data:

    1. Corrects for optical distortions introduced by the instrument optics.
    2. Corrects for differential atmospheric refraction (DAR) across the field of view.

    For IFS data, this correction is performed for each wavelength slice (under development).

    Parameters
    ----------
    input : ImagerModel or IFSCubeModel
        Input data model to correct distortion effects for.
    correct_distortion : bool
        Whether to apply distortion correction.
        Default is True.
    correct_dar : bool
        Whether to apply differential atmospheric refraction correction.
        Default is True.
    weather_output_dir : str, optional
        Path to save the weather information.
        Default is None.
    use_koa_weather : bool
        Whether to use KOA weather data if available.
        Default is True.
    
    Returns
    -------
    output
        The distortion-corrected data model (same type as input).
    """

    spec = """
        correct_distortion = boolean(default = True) # Whether to apply distortion correction.
        correct_dar = boolean(default = True) # Whether to apply differential atmospheric refraction correction
        weather_output_dir = string(default = None) # Path to save the weather information.
        use_koa_weather = boolean(default = True) # Whether to use KOA weather data if available.
    """

    class_alias = "distortion"
    calibrations = {
        'distortion' : {
            'selector': DistortionSelector,
            'selector_kwargs': {}
        }
    }

    def process(self, input):

        # Open the input data model
        input_model = self.open_model(input)

        # Initialize output model
        output_model = input_model.copy()

        # Total shifts to apply
        DY = np.zeros(input_model.data.shape, dtype=np.float32)
        DX = np.zeros(input_model.data.shape, dtype=np.float32)

        # Apply DAR correction
        if self.correct_dar:

            # Get DAR inputs at mid-point of observation
            alt_mid = (input_model.meta.target.elevation_start + input_model.meta.target.elevation_end) / 2.0
            az_mid = (input_model.meta.target.azimuth_start + input_model.meta.target.azimuth_end) / 2.0
            mjd_mid = (input_model.meta.exposure.mjd_start + input_model.meta.exposure.mjd_end) / 2.0
            obs_time = Time(mjd_mid, format='mjd', scale='utc')
            altaz_coord = AltAz(
                alt=alt_mid * u.deg,
                az=az_mid * u.deg,
                location=KECK_LOCATION,
                obstime=obs_time
            )
            wave = input_model.meta.instrument.wave_center
            scale = input_model.meta.instrument.scale
            size = input_model.data.shape
            rotation = input_model.meta.instrument.rotator_angle

            # TEMP WEATHER INFO
            temperature = 273.0  # K
            pressure = 615.0  # hPa
            humidity = 0.2  # fraction
            # weather_data = get_koa_weather_data(obs_time)
            # temperature = weather_data['temperature']
            # pressure = weather_data['pressure']
            # humidity = weather_data['humidity']

            # Calculate DAR shifts
            DY_dar, DX_dar = calc_dar_shifts(
                location=KECK_LOCATION,
                altaz_coord=altaz_coord,
                size=size,
                scale=scale,
                wave=wave,
                rotation=rotation,
                temperature=temperature,
                pressure=pressure,
                humidity=humidity,
            )
            DY += DY_dar
            DX += DX_dar

        # Apply distortion correction
        if self.correct_distortion:
            distortion_ref, _ = self.get_calibration(input_model, "distortion")
            logger.info(f"Using distortion reference {distortion_ref}")
            with self.open_model(distortion_ref) as distortion_model:
                DY += distortion_model.dy
                DX += distortion_model.dx

        # Resample the data
        output_rate, output_error = resample_distortion_drizzle(
            input_rate=input_model.data,
            input_error=input_model.err,
            input_dq=input_model.dq,
            itime=input_model.meta.exposure.exposure_time,
            dx=DX,
            dy=DY,
        )

        # Pass to the output model
        output_model.data = output_rate
        output_model.err = output_error

        # Save the weather info
        # TODO: Implement save weather data when ready.
        # if self.weather_output_dir is not None:
        #     #dark_output_path = self.make_output_path(dark_model, output_dir=self.weather_output_dir)
        #     breakpoint()

        return output_model