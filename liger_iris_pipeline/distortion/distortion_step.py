#from .. import datamodels
from ..base_step import LigerIRISStep
from .dar import calc_dar_shifts, get_koa_weather_data
from .. import datamodels
import numpy as np
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time
import astropy.units as u

from ..utils.subarray import get_subarray_model
from .resample import resample_distortion_drizzle


__all__ = ["DistortionCorrectionStep"]

KECK_LOCATION = EarthLocation.of_site('Keck Observatory')


class DistortionCorrectionStep(LigerIRISStep):
    """
    DistortionCorrectionStep: Corrects for isntrumental distortion and differential atmospheric refraction, both optional.
    Currently only supports imaging mode.
    """

    spec = """
        correct_distortion = boolean(default = True) # Whether to apply distortion correction.
        correct_dar = boolean(default = True) # Whether to apply differential atmospheric refraction correction
        weather_output_dir = string(default = None) # Path to save the weather information.
        use_koa_weather = boolean(default = True) # Whether to use KOA weather data if available.
        distortion_reference = is_string_or_datamodel(default = None) # Path to distortion reference file.
    """

    class_alias = "distortion_correction"

    def process(self, input):

        # Open the input data model
        with self.open_model(input) as input_model:

            # Initialize output
            output_model = input_model.copy()

            # Bulk shifts to apply
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
                if self.distortion_reference is None:
                    self.distortion_reference_filepath = self.get_reference_file(input_model, "distortion")
                    distortion_model = self.open_model(self.distortion_reference_filepath)
                else:
                    distortion_model = self.open_model(self.distortion_reference, copy=False)
                    self.distortion_reference_filepath = distortion_model._filepath
                self.log.info("Using distortion reference %s", distortion_model)
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
            # if self.weather_output_dir is not None:
            #     #dark_output_path = self.make_output_path(dark_model, output_dir=self.weather_output_dir)
            #     breakpoint()
            self.status = "COMPLETE"

        return output_model