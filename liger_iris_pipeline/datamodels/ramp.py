from .model_base import LigerIRISDataModel
import numpy as np
from .mixins import DefaultDQMixin, DefaultDQRawMixin


__all__ = ['RampModel', 'ProcessedRampModel']


class RampModel(DefaultDQMixin, DefaultDQRawMixin, LigerIRISDataModel):
    """
    Class for raw ramp data.

    Extensions
    ----------

    HDU Name      HDU Type  Data Type       Dimensions        Units  Description
    --------      --------  ---------       ----------        -----  ------------------------------------
    DATA          Image     UInt16/Float32  Nreads x Ny x Nx  DN     3-D ramp data array
    DQ_RAW        Image     UInt8           Nreads x Ny x Nx  None   3-D data quality array per read
    DQ            Image     UInt32          Ny x Nx           None   2-D data quality array for all reads
    SUBARRAY_MAP  Image     UInt8           Ny x Nx           None   Subarray map
    """
    schema_url = "https://oirlab.github.io/schemas/RampModel.schema"

    def on_init(self, init):
        super().on_init(init)
        self.meta.data_level = '0'

    def get_delta_readtimes(self, n_channels=None, vertical = None) -> np.ndarray:
        """
        Get the time for each read in the ramp in seconds relative to the first read.
        The start time of the first read in MJD is given by get_first_read_mjd().

        Notes
        -----
        This implementation does not model any specific instrument and is meant for testing only.

        Parameters
        ----------
        n_channels : int, optional
            Number of channels the detector is read out with.
        vertical : bool, optional
            If True, the channels are assumed to be vertical. If False, the readout channels are assumed to be horizontal.
            Within each channel, we assume the pixels are readout row by row assuming vertical channels; meaning channels are read in the width direction.

        Returns
        -------
        readtimes : np.ndarray
            1D array of length n_reads with the time of each read in seconds relative to the first read.
        """
        n_reads, ny, nx = self.data.shape

        if n_channels is None:
            n_channels = self.meta.instrument.n_channels
        if vertical is None:
            vertical = self.meta.instrument.channels_are_vertical

        if vertical:
            if nx % n_channels != 0:
                raise ValueError(
                    "nx is not divisible by n_channels. Detector size and number of channels are incompatible.")
            nx_chan = nx // n_channels
            ny_chan = ny
        else:
            if ny % n_channels != 0:
                raise ValueError(
                    "ny is not divisible by n_channels. Detector size and number of channels are incompatible.")
            ny_chan = ny // n_channels
            nx_chan = nx

        time_single_read = (ny_chan * nx_chan) / self.meta.exposure.clock_rate
        readtimes = np.arange(n_reads, dtype=np.float32) * time_single_read
        return readtimes

    def get_first_read_mjd(self, n_channels=None, vertical = None) -> np.ndarray:
        """
        Get the MJD times of the first reads for each pixel as a 2D array.

        Notes
        -----
        This implementation does not model any specific instrument and is meant for testing only.


        Parameters
        ----------
        n_channels : int, optional
            Number of channels the detector is read out with.
        vertical : bool, optional
            If True, the channels are assumed to be vertical. If False, the readout channels are assumed to be horizontal.
            Within each channel, we assume the pixels are readout row by row assuming vertical channels; meaning channels are read in the width direction.

        Returns
        -------
        first_read_mjd : np.ndarray
            2D array of shape (ny, nx) with the MJD time of the first read for each pixel.
        """

        if n_channels is None:
            n_channels = self.meta.instrument.n_channels
        if vertical is None:
            vertical = self.meta.instrument.channels_are_vertical

        if vertical:
            _data = self.data
        else:
            _data = self.data.transpose(0, 2, 1)

        n_reads, ny, nx = _data.shape

        if nx % n_channels != 0:
            raise ValueError(f"Detector size {nx} and number of channels {n_channels} are incompatible.")
        nx_chan = nx // n_channels
        ny_chan = ny

        first_read_mjd_channel = self.meta.exposure.mjd_start \
                        + np.arange(ny_chan*nx_chan, dtype=np.float32).reshape(ny_chan, nx_chan) \
                        / self.meta.exposure.clock_rate

        first_read_mjd = np.tile(first_read_mjd_channel, (1, n_channels))

        if vertical:
            return first_read_mjd
        else:
            return first_read_mjd.T
    

class ProcessedRampModel(RampModel):
    """
    Class for processed ramp data.

    Differences from RampModel:
    - Datatype for ``data`` is float32 instead of uint16.
    """
    schema_url = "https://oirlab.github.io/schemas/ProcessedRampModel.schema"