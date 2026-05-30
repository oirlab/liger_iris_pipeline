import numpy as np
import multiprocessing as mp
import ctypes
from tqdm import tqdm
# from .utils import add_refchan_ramp

from ..utils.parallelization_utils import _arraytonumpy
from multiprocessing.sharedctypes import RawArray

__all__ = ['create_ramp','generate_1overf_noise','compute_psd','generate_1overf_noise_map','compute_channel_psds','generate_1overf_noise_integrated','utr_variable_rate_cube']

# NOTE: Find a new home for this function

def _create_ramp(
    data,dq_raw,
    source : np.ndarray, # e- / s / pixel including all sources
    readtime : float = 1.7, # seconds between reads
    n_reads : int = 10,
    gain : np.ndarray | float = 1.0, # e-/ADU
    flat : np.ndarray | float = 1.0,
    bias : np.ndarray | float = 1000, # e-
    dark : np.ndarray | float = 0, # e-/s/pixel
    read_noise : np.ndarray | float = 3, # e- standard deviation
    kTC_noise : np.ndarray | float = 50, # e- standard deviation, None to skip
    nonlin_coeffs : np.ndarray | None = None,
    poisson_noise : bool = True,
    mjd_start : float = 60577.0, # MJD start time of first read of first pixel
    convert_to_uint16 : bool = True,
    clip_ramps: bool = True,
    flux_scaling: np.ndarray | None = None,
    flux_scaling_times: np.ndarray | None = None
) -> dict[str, np.ndarray]:

    if convert_to_uint16:
        _data = np.zeros(shape=(n_reads, source.shape[0], source.shape[1]), dtype=np.float32)
    else:
        _data = data

    if flux_scaling is not None and flux_scaling_times is not None:
        _source, s_mean = utr_variable_rate_cube(
            source, flux_scaling, flux_scaling_times,
            n_reads=n_reads, readtime=readtime, t0=0.0
        )
    else:
        _source = np.tile(source[None, :, :], (n_reads-1, 1, 1))  # shape (n_reads-1, ny, nx)

    # First, compute photon counts only (no read noise or bias)
    for i in np.arange(1,n_reads):
        if poisson_noise:
            _data[i, :, :] = _data[i-1, :, :] + \
                            (np.random.poisson(lam=_source[i-1] * readtime, size=source.shape)*flat +\
                            np.random.poisson(lam=dark * readtime, size=source.shape)) / gain
        else:
            _data[i, :, :] = _data[i-1, :, :] + (_source[i-1] * readtime *flat + dark * readtime) / gain

    # apply non-linear behavior
    if nonlin_coeffs is not None:
        _data[:] = np.polyval(nonlin_coeffs, _data)

    # Add read noise
    if read_noise is not None:
        _data += np.random.normal(loc=0, scale=read_noise/gain, size=_data.shape)

    # Add bias (and kTC noise if desired)
    _data += bias/gain
    if kTC_noise is not None:
        _data += np.random.normal(loc=0, scale=kTC_noise/gain, size=source.shape)[None, :, :]



    if clip_ramps:
        # Clip _data to maximum value of uint16
        _data[:] = np.clip(_data, 0, float(np.iinfo(np.uint16).max))

    if convert_to_uint16:
        # Check for negative values before returning
        if np.any(_data < 0):
            raise ValueError("Negative value found in 'data' array before returning from create_ramp. "
                             "Data needs to be all positive to be converted to np.uint16."
                             "Suggestion: Raise bias value.")

        # Round and convert to uint16
        data[:] = np.round(_data).astype(np.uint16)

    return

def _create_ramp_worker(args):
    """
    Worker function for multiprocessing. Runs create_ramp on a block of rows.
    Args:
        args (tuple): (source_block, readtime, n_reads, gain_block, flat_block, bias_block, dark_block, read_noise,
        kTC_noise, nonlin_coeffs, poisson_noise, mjd_start, convert_to_uint16, clip_ramps, types_tuple,myrandomseed,
        flux_scaling,flux_scaling_times)
    Returns:
        dict[str, np.ndarray]: Output from create_ramp for the block
    """
    (block_start, block_end, readtime, n_reads, nonlin_coeffs, poisson_noise, mjd_start, convert_to_uint16, clip_ramps,
     types_tuple,myrandomseed,flux_scaling,flux_scaling_times) = args
    mp_data_type, mp_float_type, mp_dq_raw_type = types_tuple

    np.random.seed(myrandomseed)

    data_np = _arraytonumpy(shared_data, shared_data_shape, dtype=mp_data_type)
    dq_raw_np = _arraytonumpy(shared_dq_raw, shared_dq_raw_shape, dtype=mp_dq_raw_type)
    source_np = _arraytonumpy(shared_source, shared_source_shape, dtype=mp_float_type)
    gain_np = _arraytonumpy(shared_gain, shared_gain_shape, dtype=mp_float_type)
    flat_np = _arraytonumpy(shared_flat, shared_flat_shape, dtype=mp_float_type)
    bias_np = _arraytonumpy(shared_bias, shared_bias_shape, dtype=mp_float_type)
    dark_np = _arraytonumpy(shared_dark, shared_dark_shape, dtype=mp_float_type)
    read_noise_np = _arraytonumpy(shared_read_noise, shared_read_noise_shape, dtype=mp_float_type)
    kTC_noise_np = _arraytonumpy(shared_kTC_noise, shared_kTC_noise_shape, dtype=mp_float_type)

    outputs = _create_ramp(
        data_np[:,block_start:block_end, :],
        dq_raw_np[:,block_start:block_end, :],
        source=source_np[block_start:block_end, :],
        readtime=readtime,
        n_reads=n_reads,
        gain=gain_np[block_start:block_end, :],
        flat=flat_np[block_start:block_end, :],
        bias = bias_np[block_start:block_end, :],
        dark = dark_np[block_start:block_end, :],
        read_noise = read_noise_np[block_start:block_end, :],
        kTC_noise = kTC_noise_np[block_start:block_end, :],
        nonlin_coeffs = nonlin_coeffs,
        poisson_noise = poisson_noise,
        mjd_start = mjd_start,
        convert_to_uint16 = convert_to_uint16,
        clip_ramps = clip_ramps,
        flux_scaling=flux_scaling,
        flux_scaling_times=flux_scaling_times
    )

    return (block_start, block_end)


def create_ramp(
    source : np.ndarray,
    readtime : float = 1.7,
    n_reads : int = 10,
    gain : np.ndarray | float = 1.0,
    flat : np.ndarray | None = None,
    bias : np.ndarray | float = 1000,
    dark : np.ndarray | float = 0,
    read_noise : float | None = 3,
    kTC_noise : float | None = 50,
    nonlin_coeffs : np.ndarray | None = None,
    poisson_noise : bool = True,
    mjd_start : float = 60577.0,
    convert_to_uint16 : bool = True,
    clip_ramps: bool = True,
    max_cores: int = 1,
    block_size: int | None = None,
    std_1overf: float | None = None, # e-
    n_channels: int | None = None,
    vertical: bool = True,
    flux_scaling: np.ndarray | None = None,
    flux_scaling_times: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """
    Simulate a detector up-the-ramp (UTR) readout sequence for a given source image.

    Parameters
    ----------
    source : np.ndarray
        2D array of source signal (e-/s/pixel) including all sources.
    readtime : float
        Time between reads (seconds).
    n_reads : int
        Number of reads in the ramp sequence (default: 10).
    gain : None or float or np.ndarray
        Gain of the detector (e-/ADU).
    flat : None or float or np.ndarray, optional
        Flat field array (default: None).
        We assume that flats have been corrected for gain variations already. In this function the gain is applied after the flat, but in the data reduction pipeline the gain correction should be applied first.
    bias : None or float or np.ndarray, optional
        Bias level to add to the first read (default: 1000 e-).
    dark : None or flat or np.ndarray, optional
        Dark current level to add to each read (e-/s/pixel) (default: 0)
        The flat field is applied BEFORE adding the dark current. This is because dark subtraction is typically done before the flat fielding step.
    read_noise : None or float or np.ndarray, optional
        Standard deviation of read noise (e-) for each read (default: 3 e-).
    kTC_noise : None or float or np.ndarray, optional
        kTC noise parameter (e-) to add to the first read (default: 50 e-).
    nonlin_coeffs : np.ndarray or None, optional
        Nonlinearity correction coefficients (default: None). Applies as data = np.polyval(nonlin_coeffs, data).
    poisson_noise : bool, optional
        If True, apply Poisson noise to the signal (default: True).
    mjd_start : float, optional
        Modified Julian Date for the start time (default: 60577.0).
    convert_to_uint16 : bool, optional
        If True, round and convert the output data to np.uint16 (default: True).
    clip_ramps: bool, optional
        If True, clip_ramps the output data to the range of np.uint16 (0 to 65535) (default: True).
    max_cores : int, optional
        Maximum number of CPU cores to use for parallel processing (default: 1).
    block_size : int or None, optional
        Number of rows to process in each block when using multiple cores (default: None).
    std_1overf : float or None, optional
        Standard deviation of 1/f noise in ADU (ie, DN). If None, 1/f noise is not added (default: None).
    n_channels : n_channels,
        Number of readout channels. If None, assume 1 channel (default: None).
    vertical : bool, optional
        If True, channels are vertical; if False, channels are horizontal (default: True).
    flux_scaling : np.ndarray or None, optional
        Timeseries of flux to model variability centered on unity (default: None). Should match length of flux_scaling_times.
    flux_scaling_times : np.ndarray or None, optional
        Times corresponding to flux_scaling array (seconds) (default: None).

    Returns
    -------
    dict[str, np.ndarray]
        Dictionary containing:
            - 'times': astropy.table.Table of read numbers, times, and exptimes
            - 'data': 3D array (n_reads, ny, nx) of ramp data
            - 'dq': 3D array (n_reads, ny, nx) of data quality flags

    Raises
    ------
    ValueError
        If any value in the output 'data' array is negative.
    """
    ny, nx = source.shape

    if gain is None:
        gain = 1.0
    if flat is None:
        flat = 1.0
    if bias is None:
        bias = 1000
    if dark is None:
        dark = 0
    if read_noise is None:
        read_noise = 0
    if kTC_noise is None:
        kTC_noise = 0


    # Run in parallel
    if max_cores > 1:

        if convert_to_uint16:
            mp_data_type = ctypes.c_ushort
        else:
            mp_data_type = ctypes.c_float
        mp_float_type = ctypes.c_float
        mp_dq_raw_type = ctypes.c_uint8

        types_tuple = (mp_data_type, mp_float_type, mp_dq_raw_type)

        data_mp = RawArray(mp_data_type, nx * ny * n_reads)
        data_shape = (n_reads, ny, nx)
        data_np = _arraytonumpy(data_mp, data_shape, dtype=mp_data_type)

        dq_raw_mp = RawArray(mp_dq_raw_type, nx * ny * n_reads)
        dq_raw_shape = (n_reads, ny, nx)
        dq_raw_np = _arraytonumpy(dq_raw_mp, dq_raw_shape, dtype=mp_dq_raw_type)

        source_mp = RawArray(mp_float_type, nx * ny)
        source_shape = (ny, nx)
        source_np = _arraytonumpy(source_mp, source_shape, dtype=mp_float_type)
        source_np[:] = source

        gain_mp = RawArray(mp_float_type, nx * ny)
        gain_shape = (ny, nx)
        gain_np = _arraytonumpy(gain_mp, gain_shape, dtype=mp_float_type)
        if not isinstance(gain, np.ndarray):
            gain_np[:]  = np.full(source.shape, gain, dtype=np.float32)
        else:
            gain_np[:] = gain.astype(np.float32)

        flat_mp = RawArray(mp_float_type, nx * ny)
        flat_shape = (ny, nx)
        flat_np = _arraytonumpy(flat_mp, flat_shape, dtype=mp_float_type)
        if not isinstance(flat, np.ndarray):
            flat_np[:] = np.full(source.shape, flat, dtype=np.float32)
        else:
            flat_np[:] = flat


        bias_mp = RawArray(mp_float_type, nx * ny)
        bias_shape = (ny, nx)
        bias_np = _arraytonumpy(bias_mp, bias_shape, dtype=mp_float_type)
        if not isinstance(bias, np.ndarray):
            bias_np[:] = np.full(source.shape, bias, dtype=np.float32)
        else:
            bias_np[:] = bias

        dark_mp = RawArray(mp_float_type, nx * ny)
        dark_shape = (ny, nx)
        dark_np = _arraytonumpy(dark_mp, dark_shape, dtype=mp_float_type)
        if not isinstance(dark, np.ndarray):
            dark_np[:] = np.full(source.shape, dark, dtype=np.float32)
        else:
            dark_np[:] = dark

        read_noise_mp = RawArray(mp_float_type, nx * ny)
        read_noise_shape = (ny, nx)
        read_noise_np = _arraytonumpy(read_noise_mp, read_noise_shape, dtype=mp_float_type)
        if not isinstance(read_noise, np.ndarray):
            read_noise_np[:] = np.full(source.shape, read_noise, dtype=np.float32)
        else:
            read_noise_np[:] = read_noise


        kTC_noise_mp = RawArray(mp_float_type, nx * ny)
        kTC_noise_shape = (ny, nx)
        kTC_noise_np = _arraytonumpy(kTC_noise_mp, kTC_noise_shape, dtype=mp_float_type)
        if not isinstance(kTC_noise, np.ndarray):
            kTC_noise_np[:] = np.full(source.shape, kTC_noise, dtype=np.float32)
        else:
            kTC_noise_np[:] = kTC_noise

        if block_size is None:
            block_size = max(1, ny // (4*max_cores)) if max_cores > 1 else ny

        # Prepare blocks
        args_list = []
        for block_start in range(0, ny, block_size):
            block_end = min(block_start + block_size, ny)

            # This is almost certainly not the best way to handle RNG seeds in multiprocessing,
            # but it will at least ensure different seeds for each worker and I understand it.
            myrandomseed = np.random.default_rng().integers(
                low=0,
                high=np.iinfo(np.uint32).max,
                dtype=np.uint32
            )

            args = (block_start, block_end,
                    readtime,
                    n_reads,
                    nonlin_coeffs,
                    poisson_noise,
                    mjd_start,
                    convert_to_uint16,
                    clip_ramps,
                    types_tuple,
                    myrandomseed,
                    flux_scaling,flux_scaling_times
                    )
            args_list.append(args)

        _init_args = (data_mp, data_shape,
                dq_raw_mp, dq_raw_shape,
                source_mp, source_shape,
                gain_mp, gain_shape,
                flat_mp, flat_shape,
                bias_mp, bias_shape,
                dark_mp, dark_shape,
                read_noise_mp, read_noise_shape,
                kTC_noise_mp, kTC_noise_shape
                      )
        tpool = mp.Pool(processes=max_cores, initializer=_tpool_init,
                        initargs=_init_args, maxtasksperchild=50)
        tasks = [tpool.apply_async(_create_ramp_worker, args=(_args,))
                 for _args in args_list]

        for t in tqdm(tasks, desc="Processing blocks"):
            t.wait()

        print("Closing threadpool")
        tpool.close()
        tpool.join()

    else:
        data_np = np.zeros(shape=(n_reads, source.shape[0], source.shape[1]), dtype=np.float32)
        dq_raw_np = np.zeros(shape=(n_reads, source.shape[0], source.shape[1]), dtype=np.uint8)
        _outputs = _create_ramp(
            data_np, dq_raw_np,
            source=source,
            readtime=readtime,
            n_reads=n_reads,
            gain=gain,
            flat=flat,
            bias=bias,
            dark=dark,
            read_noise=read_noise,
            kTC_noise=kTC_noise,
            nonlin_coeffs=nonlin_coeffs,
            poisson_noise=poisson_noise,
            mjd_start=mjd_start,
            convert_to_uint16=convert_to_uint16,
            clip_ramps=clip_ramps,
            flux_scaling=flux_scaling,
            flux_scaling_times=flux_scaling_times
        )

    if n_channels is None:
        n_channels = 1

    clock_rate = 1/(readtime/((nx*ny)//n_channels)) # in Hz
    # _meta = dict(clock_rate=clock_rate,
    #              mjd_start=mjd_start,
    #              n_channels=n_channels,
    #              channels_are_vertical=vertical,
    #              n_refpixs = 4)
    _meta = {
        'exposure.clock_rate': clock_rate,
        'exposure.mjd_start': mjd_start,
        'instrument.n_channels': n_channels,
        'instrument.channels_are_vertical': vertical,
        'instrument.n_refpixs': 4
    }

    if std_1overf is not None  and std_1overf > 0:
        noise_1overf = generate_1overf_noise_map(data_np.shape, n_channels, vertical, clock_rate, std_1overf)
        data_np += noise_1overf

    if convert_to_uint16:
        data_np = np.round(data_np).astype(np.uint16)

    _outputs = dict(data=data_np, dq_raw=dq_raw_np, meta=_meta)

    return _outputs

def _tpool_init(data, data_shape,
                dq_raw, dq_raw_shape,
                source, source_shape,
                gain, gain_shape,
                flat, flat_shape,
                bias, bias_shape,
                dark, dark_shape,
                read_noise, read_noise_shape,
                kTC_noise, kTC_noise_shape
                ):
    """
    Initializer function for the thread pool that initializes various shared variables. Main things to note that all
    except the shapes are shared arrays (mp.Array).
    """
    global shared_data, shared_data_shape, \
        shared_dq_raw, shared_dq_raw_shape, \
        shared_source, shared_source_shape, \
        shared_gain, shared_gain_shape, \
        shared_flat, shared_flat_shape, \
        shared_bias, shared_bias_shape, \
        shared_dark, shared_dark_shape, \
        shared_read_noise, shared_read_noise_shape, \
        shared_kTC_noise, shared_kTC_noise_shape

    shared_data = data
    shared_data_shape = data_shape

    shared_dq_raw = dq_raw
    shared_dq_raw_shape = dq_raw_shape

    shared_source = source
    shared_source_shape = source_shape

    shared_gain = gain
    shared_gain_shape = gain_shape

    shared_flat = flat
    shared_flat_shape = flat_shape

    shared_bias = bias
    shared_bias_shape = bias_shape

    shared_dark = dark
    shared_dark_shape = dark_shape

    shared_read_noise = read_noise
    shared_read_noise_shape = read_noise_shape

    shared_kTC_noise = kTC_noise
    shared_kTC_noise_shape = kTC_noise_shape

def generate_1overf_noise_map(shape_3d, n_channels=1, vertical=True, clock_rate=1.0, std_1overf=1.0, seed=None):
    """
    Generate a 3D array of 1/f (pink) noise assuming same noise in each readout channel.

    Parameters
    ----------
    shape_3d : tuple of int
        Shape of the output array (n_reads, ny, nx).
    n_channels : int, optional
        Number of readout channels (default: 1).
    vertical : bool, optional
        If True, channels are vertical; if False, channels are horizontal.
    clock_rate : float, optional
        Clock rate in Hz (samples per second).
    std_1overf : float, optional
        Desired standard deviation of the output time series.
    seed : int or None, optional
        Random seed for reproducibility.

    Returns
    -------
    ndarray
        3D array of shape (n_reads, ny, nx) containing 1/f noise with the same noise pattern in each readout channel.

    """
    n_reads, ny, nx = shape_3d

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
        nx_chan = ny // n_channels
        ny_chan = nx

    noise_1overf_channel = generate_1overf_noise(n=(n_reads * nx_chan * ny_chan),
                                                 dt=1/clock_rate,
                                                 std=std_1overf,
                                                 seed=seed)
    noise_1overf_channel = noise_1overf_channel.reshape(n_reads, ny_chan, nx_chan)

    noise_1overf = np.tile(noise_1overf_channel, (1, 1, n_channels))

    if vertical:
        return noise_1overf
    else:
        return noise_1overf.transpose(0, 2, 1)

def generate_1overf_noise(n, dt=1.0, std=1.0, seed=None, return_time=False):
    """
    Generate a 1/f (pink) noise time series using frequency-domain synthesis.

    Notes
    -----
    Generated from ChatGPT.

    Parameters
    ----------
    n : int
        Number of samples in the time series.
    dt : float, optional
        Time sampling interval.
    std : float, optional
        Desired standard deviation of the output time series.
    seed : int or None, optional
        Random seed for reproducibility.
    return_time : bool, optional
        If True, also return the time sampling vector.

    Returns
    -------
    noise : ndarray, shape (n,)
        Real-valued 1/f noise time series.
    t : ndarray, shape (n,), optional
        Time sampling vector (returned if return_time=True).
    """
    rng = np.random.default_rng(seed)

    # Fourier frequencies (positive only, real FFT)
    freqs = np.fft.rfftfreq(n, d=dt)

    # Avoid division by zero at DC
    scale = np.zeros_like(freqs)
    nonzero = freqs > 0
    scale[nonzero] = 1.0 / np.sqrt(freqs[nonzero])

    # Random complex spectrum
    real = rng.normal(size=freqs.size)
    imag = rng.normal(size=freqs.size)
    spectrum = (real + 1j * imag) * scale

    # Enforce zero DC component
    spectrum[0] = 0.0

    # Inverse FFT to time domain
    noise = np.fft.irfft(spectrum, n=n)

    # Normalize to requested standard deviation
    noise -= np.mean(noise)
    noise *= std / np.std(noise)

    if return_time:
        t = np.arange(n) * dt
        return noise, t

    return noise

def generate_1overf_noise_integrated(
    n,
    dt=1.0,
    readtime=1.0,
    std=1.0,
    seed=None,
    return_time=False,
    mode="same",
):
    """
    Generate a 1/f (pink) noise time series sampled at dt and convolved with a
    top-hat (boxcar) kernel of width ``readtime`` to emulate finite integration time.

    Conceptually, this produces a *time-averaged* version of the underlying 1/f noise:
    y(t) = (1/readtime) Integral_{t-readtime/2}^{t+readtime/2} x(u) du
    when using a centered boxcar and ``mode="same"``.

    Notes
    -----
    Generated from ChatGPT.

    Parameters
    ----------
    n : int
        Number of samples in the output time series (sampled at dt).
    dt : float, optional
        Time sampling interval of the generated series. Should satisfy dt << readtime
        for a good approximation of continuous-time integration.
    readtime : float, optional
        Integration time (width of the top-hat) in the same time units as dt.
    std : float, optional
        Desired standard deviation of the *final (convolved)* output time series.
    seed : int or None, optional
        Random seed for reproducibility.
    return_time : bool, optional
        If True, also return the time sampling vector.
    mode : {"same","full","valid"}, optional
        Convolution mode passed to np.convolve. Default "same" returns length n.

    Returns
    -------
    noise_int : ndarray
        The convolved (time-averaged) 1/f noise series. Length depends on ``mode``
        ("same" -> n).
    t : ndarray, optional
        Time vector corresponding to the returned samples (returned if return_time=True).

    Notes
    -----
    - The top-hat kernel is *normalized* (sum=1), so it implements a moving average
      over approximately ``readtime``.
    - The output is normalized to have standard deviation ``std`` *after* convolution.
    - Edge behavior depends on ``mode``. For "same", the result uses the implicit
      zero-padding behavior of np.convolve; if you want different boundary handling
      (reflect/nearest), you can pad manually before convolution.
    """
    if n <= 0:
        raise ValueError("n must be a positive integer.")
    if dt <= 0:
        raise ValueError("dt must be > 0.")
    if readtime <= 0:
        raise ValueError("readtime must be > 0.")
    if mode not in ("same", "full", "valid"):
        raise ValueError('mode must be one of {"same","full","valid"}.')

    # Generate underlying 1/f noise at fine sampling dt
    base = generate_1overf_noise(n, dt=dt, std=1.0, seed=seed, return_time=False)

    # Top-hat kernel width in samples (at least 1)
    w = int(np.round(readtime / dt))
    w = max(w, 1)

    # Normalized boxcar (moving average) kernel
    kernel = np.ones(w, dtype=float) / w

    # Convolve to emulate finite integration time
    noise_int = np.convolve(base, kernel, mode=mode)

    # Normalize to requested std (after convolution)
    noise_int -= np.mean(noise_int)
    sigma = np.std(noise_int)
    if sigma > 0:
        noise_int *= std / sigma
    else:
        # Extremely unlikely, but keep behavior defined
        noise_int[:] = 0.0

    if return_time:
        # Time vector must match output length (depends on convolution mode)
        if mode == "same":
            t = np.arange(n) * dt
        elif mode == "full":
            t = np.arange(n + w - 1) * dt
        else:  # "valid"
            t = np.arange(max(n - w + 1, 0)) * dt
        return noise_int, t

    noise_int = np.clip(noise_int,0,None)
    return noise_int

def compute_psd(x, dt=1.0, detrend=False, onesided=True):
    """
    Compute the power spectral density (PSD) of a time series using an FFT
    periodogram.

    Notes: generated from ChatGPT

    Parameters
    ----------
    x : array_like, shape (n,)
        Input time series.
    dt : float, optional
        Time sampling interval.
    detrend : bool, optional
        If True, subtract the mean before computing the PSD.
    onesided : bool, optional
        If True, return the one-sided PSD (recommended for real signals).

    Returns
    -------
    freqs : ndarray
        Fourier frequencies.
    psd : ndarray
        Power spectral density corresponding to ``freqs``.
    """
    x = np.asarray(x)
    n = x.size

    if detrend:
        x = x - np.mean(x)

    # FFT
    fft = np.fft.rfft(x) if onesided else np.fft.fft(x)

    # Frequency axis
    freqs = np.fft.rfftfreq(n, d=dt) if onesided else np.fft.fftfreq(n, d=dt)

    # Periodogram normalization
    psd = (np.abs(fft) ** 2) * (dt / n)

    # One-sided correction (except DC and Nyquist)
    if onesided and n % 2 == 0:
        psd[1:-1] *= 2.0
    elif onesided:
        psd[1:] *= 2.0

    return freqs, psd



def compute_channel_psds(cube, n_channels=1, vertical=True, clock_rate=1.0,detrend=False, onesided=True):
    """
    Compute one power spectral density (PSD) per readout channel from a 3D
    up-the-ramp datacube by flattening each channel into a 1D readout-ordered
    time series.

    This implementation effectively assumes that no signal is present in the data other than noise.

    For each readout channel, the data are reshaped into a single 1D array
    using NumPy's default (C-order) memory layout, such that the ordering of
    samples matches the implicit readout order used when generating channel-
    correlated 1/f noise. The PSD of this 1D sequence is then computed using
    `compute_psd`.

    Parameters
    ----------
    cube : ndarray, shape (n_reads, ny, nx)
        Up-the-ramp datacube.
    n_channels : int, optional
        Number of detector readout channels. The detector dimension
        corresponding to the channel direction must be divisible by
        ``n_channels``.
    vertical : bool, optional
        If True, channels are assumed to be vertical stripes along the x
        dimension. If False, channels are assumed to be horizontal stripes
        along the y dimension.
    clock_rate : float, optional
        Clock rate in Hz (samples per second).
    detrend : bool, optional
        If True, subtract the mean of each channel time series before
        computing the PSD.
    onesided : bool, optional
        If True, compute a one-sided PSD appropriate for real-valued data.

    Returns
    -------
    freqs : ndarray
        Fourier frequency grid corresponding to the PSD.
    psd_channels : ndarray, shape (n_channels, n_freq)
        Power spectral density for each readout channel, computed from the
        flattened channel data.
    """
    if cube.ndim != 3:
        raise ValueError("cube must have shape (n_reads, ny, nx).")

    if n_channels < 1:
        raise ValueError("n_channels must be >= 1.")

    if vertical:
        _cube = cube
    else:
        _cube = cube.transpose(0, 2, 1)

    n_reads, ny, nx = _cube.shape
    if nx % n_channels != 0:
        raise ValueError("Dimensions is not divisible by n_channels.")
    nx_chan = nx // n_channels

    psd_channels = []
    for ic in range(n_channels):
        x0 = ic * nx_chan
        x1 = (ic + 1) * nx_chan
        chan = _cube[:, :, x0:x1]

        freqs, psd_chan = compute_psd(chan.ravel(), dt=1/clock_rate, detrend=detrend, onesided=onesided)

        psd_channels.append(psd_chan)

    return freqs, np.asarray(psd_channels)



def utr_variable_rate_cube(
        source: np.ndarray,
        flux_scaling: np.ndarray,
        flux_scaling_times: np.ndarray,
        n_reads: int,
        readtime: float,
        t0: float = 0.0,
):
    """
    Build a (n_reads-1, ny, nx) cube of per-read *average* electron rates
    for a time-variable UTR ramp, conserving total flux.

    Parameters
    ----------
    source : ndarray, shape (ny, nx)
        Average electron rate map (e-/s), averaged over the full exposure.
    flux_scaling : ndarray, shape (nt,)
        Dimensionless flux scaling vs time (mean ~ 1).
    flux_scaling_times : ndarray, shape (nt,)
        Time samples in seconds (assumed monotonic).
    n_reads : int
        Total number of reads (including the first zero-count read).
    readtime : float
        Time between reads in seconds.
    t0 : float, optional
        Start time of the ramp.

    Returns
    -------
    rate_cube : ndarray, shape (n_reads-1, ny, nx)
        Average e-/s rate map for each read interval.
    scaling_mean_per_read : ndarray, shape (n_reads-1,)
        Mean flux scaling applied during each interval.
    """

    if source.ndim != 2:
        raise ValueError("source must be 2D (ny, nx).")
    if flux_scaling.ndim != 1:
        raise ValueError("flux_scaling must be 1D.")
    if flux_scaling_times.ndim != 1:
        raise ValueError("flux_scaling_times must be 1D.")
    if flux_scaling.size != flux_scaling_times.size:
        raise ValueError("flux_scaling and flux_scaling_times must match in size.")
    if n_reads < 2:
        raise ValueError("n_reads must be >= 2.")

    ny, nx = source.shape
    T = (n_reads - 1) * readtime

    # Read boundaries
    read_edges = t0 + np.arange(n_reads) * readtime

    # Integration grid: union of read edges and provided samples
    t_grid = np.unique(
        np.concatenate([read_edges, flux_scaling_times])
    )

    # Restrict to the modeled exposure window
    mask = (t_grid >= t0) & (t_grid <= t0 + T)
    t_grid = t_grid[mask]

    # Interpolate scaling onto integration grid
    scaling_grid = np.interp(
        t_grid,
        flux_scaling_times,
        flux_scaling,
        left=flux_scaling[0],
        right=flux_scaling[-1],
    )

    # Integral over each read interval
    interval_integrals = np.empty(n_reads - 1, dtype=float)

    for i in range(n_reads - 1):
        t_lo = read_edges[i]
        t_hi = read_edges[i + 1]

        sel = (t_grid >= t_lo) & (t_grid <= t_hi)
        interval_integrals[i] = np.trapz(
            scaling_grid[sel],
            t_grid[sel]
        )

    # Enforce flux conservation over the whole exposure
    total_integral = np.sum(interval_integrals)
    norm = T / total_integral

    # Mean scaling per read
    scaling_mean_per_read = norm * interval_integrals / readtime

    # Build rate cube
    rate_cube = source[None, :, :] * scaling_mean_per_read[:, None, None]

    return rate_cube, scaling_mean_per_read