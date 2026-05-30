from . import fit_gain_Brandt
from ..ramp_fitting import fitramp_Brandt
from ..stpipe.base_step import LigerIRISStep
from .. import datamodels
import numpy as np
from typing import Sequence
from ..utils.stats import get_err_from_posterior
from ..datamodels.dqflags import DQ_FLAGS
from ..calibrations import GainSelector, ReadNoiseSelector

import multiprocessing as mp
import ctypes
from ..utils.parallelization_utils import _arraytonumpy, numba_thread_scope
from multiprocessing.sharedctypes import RawArray
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)


__all__ = ['MakeGainStep']

SATURATED_FLAG_uint8 =  np.uint8(DQ_FLAGS["SATURATED"])
DO_NOT_USE_FLAG_uint8 = np.uint8(DQ_FLAGS["DO_NOT_USE"])
JUMP_DET_FLAG_uint8 = np.uint8(DQ_FLAGS["JUMP_DET"])

class MakeGainStep(LigerIRISStep):
    """
    Estimate the detector electronic gain (and optionally read noise) from up-the-ramp data.

    This step fits detector gain and, optionally, read noise parameters
    from raw up-the-ramp (UTR) ramps using the maximum-likelihood framework
    described in Brandt (2025; PASP, 137, 125006). Three fitting strategies are
    supported: a grid-based maximum-likelihood search, a local quadratic
    approximation, or a hybrid approach that uses the grid search to locate
    the optimum and then refines it with a quadratic approximation.

    Initial gain and read-noise values may be provided explicitly (e.g., as
    arrays defining a search grid). If not provided, the step is
    expected to obtain appropriate defaults from the calibration database.
    Optional arguments allow fixing the read noise while fitting only the
    gain, and treating all ramps as having identical count rates.
    
    The fitting may be performed on a per-pixel basis or using a single
    model for the full detector. Although the full detector mode is only for
    testing.

    Parameters
    ----------
    input : list of str or list of RampModel
        List of input file paths or ramp models to process.
    max_cores : int, optional
        Maximum number of CPU cores to use.
        Default is 1.
    init_gain : None or array-like, optional
        Initial gain value(s) used to define the maximum-likelihood grid search. If None, obtain an initial value from the calibration database. If provided, this may be a scalar or an array defining the gain sampling (e.g., ``np.linspace(0.1, 10, 101)``). Default is None.
    init_RN : None or array-like, optional
        Initial read noise value(s) used to define the maximum-likelihood grid search. If None, obtain an initial value from the calibration database. If provided, this may be a scalar or an array defining the read-noise sampling (e.g., ``np.linspace(1, 20, 101)``). Default is None.
    mode : {'per_pixel', 'channel', 'full_detector'}, optional
        Mode used to fit the parameters. ``'per_pixel'`` fits independent parameters for each pixel. ``'full_detector'`` fits a single set of parameters for the detector. ``'channel'`` is reserved for future implementation. Default is 'per_pixel'.
    method : {'quad', 'grid', 'both'}, optional
        Fitting strategy. ``'grid'`` performs a maximum-likelihood grid search. ``'quad'`` uses a quadratic approximation around the initial parameters. ``'both'`` runs a grid search first and then refines the solution with a quadratic approximation. Default is 'quad'.
    init_delta_gains : array-like or None, optional
        Gain grid offsets used for the maximum-likelihood grid search. The gain sampling is defined as ``init_gain + init_delta_gains``. Default is None.
    init_delta_RNs : array-like or None, optional
        Read-noise grid offsets used for the maximum-likelihood grid search. The read-noise sampling is defined as ``init_RN + init_delta_RNs``. Default is None.
    quad_delta_gain : float, optional
        Only used when ``method='quad'``. Defines the initial gain step size around ``init_gain`` for the quadratic approximation. Default is 0.2.
    quad_delta_RN : float, optional
        Only used when ``method='quad'``. Defines the initial read-noise step size around ``init_RN`` for the quadratic approximation. Default is 0.5.
    fix_RN : bool, optional
        If True, fix the read noise to ``init_RN`` and fit only the gain. Default is False.
    countratesidentical : bool, optional
        If True, assume all ramps have identical count rates. Default is False.

    Returns
    -------
    output : GainModel
        Gain model containing the fitted gain (and, if applicable, read noise).

    References
    ----------
    Brandt, T. D. (2025), *Computing the Electronic Gain for Detectors Read Out Up-the-ramp*, PASP, 137, 125006.
    https://ui.adsabs.harvard.edu/abs/2025PASP..137l5006B/abstract

    Roman calibration pipeline reference:
    https://github.com/spacetelescope/romancal
    """

    spec = """
        init_gain = is_string_or_datamodel(default=None) # Initial gain value used for the maximum likelihood grid search. If None, use calibration database.
        init_RN = is_string_or_datamodel(default=None) # Initial readnoise value used for the maximum likelihood grid search. If None, use calibration database.
        mode = option('per_pixel', 'channel', 'full_detector', default='per_pixel') # Mode to fit the parameters: 'per_pixel', 'channel', or 'full_detector'.
        method = option('quad', 'grid', 'both', default='quad') # Method to fit the parameters: 'quad' for quadratic approximation, 'grid' for maximum likelihood grid search, 'both' for both methods.
        init_delta_gains = float_list(default=None) # Grid sampling defined as init_gain + init_delta_gains for the maximum likelihood grid search.
        init_delta_gain_start = float(default=-1)  # Initial value for the gain grid search.
        init_delta_gain_step = float(default=0.02)  # Step size for the gain grid search.
        init_delta_gain_stop = float(default=1)  # Final value for the gain grid search.
        init_delta_RN_start = float(default=-10)  # Initial value for the read-noise grid search.
        init_delta_RN_step = float(default=0.4)  # Step size for the read-noise grid search.
        init_delta_RN_stop = float(default=10)  # Final value for the read-noise grid search.
        quad_delta_gain = float(default=0.2) # Used only in 'quad' mode, defines the initial delta gain around init_gain for the quadratic approximation.
        quad_delta_RN = float(default=0.5) # Used only in 'quad' mode, defines the initial delta read noise around init_RN for the quadratic approximation.
        fix_RN = boolean(default=False) # If True, fix the read noise to init_RN value and only fit for gain.
        countratesidentical = boolean(default=False) # If True, assume all ramps have identical count rates.
        suffix = string(default='')
    """

    calibrations = {
        'init_gain' : {
            'selector' : GainSelector,
            'selector_kwargs' : {}
        },
        'init_RN' : {
            'selector' : ReadNoiseSelector,
            'selector_kwargs' : {}
        },
    }
    class_alias = "make_gain"

    def process(self, input):
        if self.mode.lower() != 'full_detector' and self.mode.lower() != 'per_pixel':
            raise NotImplementedError(f"Only 'full_detector' and 'per_pixel' modes are implemented currently. Not {self.mode}")

        if isinstance(input, (datamodels.LigerIRISDataModel, str)):
            _input_list_tmp = [input]
        if  isinstance(input, Sequence):
            _input_list_tmp = input
        nfiles = len(_input_list_tmp)
        logger.info(f"Deriving the detector gain from a list of {nfiles} inputs.")

        input_models = [self.open_model(f) for f in _input_list_tmp]
        datamodel0 = input_models[0]
        nreads,ny,nx = datamodel0.data.shape

        if self.init_gain is None:
            gain_init, _ = self.get_calibration(datamodel0, 'init_gain')
            gain_init_model = self.open_model(gain_init)
            _init_center_gain = gain_init_model.gain
            logger.info(f"Using {gain_init} as initial detector gain values with median value {np.nanmedian(_init_center_gain)}.")
        elif isinstance(self.init_gain, float):
            _init_center_gain = self.init_gain
            logger.info(f"Using user-defined initial detector gain values: {self.init_gain}.")
        elif isinstance(self.init_gain, np.ndarray):
            _init_center_gain = self.init_gain
            logger.info(f"Using user-defined initial detector gain array with median value {np.nanmedian(_init_center_gain)}.")
        elif isinstance(self.init_gain, datamodels.GainModel):
            _init_center_gain = self.init_gain.gain
            logger.info(f"Using user-defined initial detector gain model with median value {np.nanmedian(_init_center_gain)}.")

        if self.init_RN is None:
            rn_cal_init, _ = self.get_calibration(datamodel0, 'init_RN')
            rn_model_init = self.open_model(rn_cal_init)
            _init_center_RN = rn_model_init.rn
            logger.info(f"Using {rn_cal_init} as initial read noise values with median value {np.nanmedian(_init_center_RN)} DN.")
        elif isinstance(self.init_RN, float):
            _init_center_RN = self.init_RN
            logger.info(f"Using user-defined initial read noise values: {self.init_RN}.")
        elif isinstance(self.init_RN, np.ndarray):
            _init_center_RN = self.init_RN
            logger.info(f"Using user-defined initial read noise array with median value {np.nanmedian(_init_center_RN)} DN.")
        elif isinstance(self.init_RN, datamodels.ReadNoiseModel):
            _init_center_RN = self.init_RN.rn
            logger.info(f"Using user-defined initial read noise model with median value {np.nanmedian(_init_center_RN)} DN.")
        delta_readtimes = datamodel0.get_delta_readtimes()

        if self.method == 'quad':
            _init_delta_gains = np.array([-self.quad_delta_gain,0,+self.quad_delta_gain])
            if self.fix_RN:
                _init_delta_RNs = None
            else:
                _init_delta_RNs = np.array([-self.quad_delta_RN,0,+self.quad_delta_RN])
        elif self.method == 'grid' or self.method == 'both':
            _init_delta_gains = np.arange(
                self.init_delta_gain_start,
                self.init_delta_gain_stop + self.init_delta_gain_step,
                self.init_delta_gain_step
            )
            if self.fix_RN:
                _init_delta_RNs = None
            else:
                _init_delta_RNs = np.arange(
                    self.init_delta_RN_start,
                    self.init_delta_RN_stop + self.init_delta_RN_step,
                    self.init_delta_RN_step
                )

        if self.mode.lower() == 'full_detector':
            logger.info(f"Running in full_detector mode. All detector pixels will be fitted jointly and a single gain and/or readnoise value will be returned for the entire chip.")
        elif self.mode.lower() == 'per_pixel':
            logger.info(f"Running in single_pixel mode. Each detector pixel will be fitted independently and a map of gain and/or readnoise will be returned.")
            
        # Define output model from inputs
        output_gain = datamodels.GainModel.from_datamodels(input_models)

        # Make all ramps from all files into a big cube
        ramp_arr = []
        dq_raw_arr = []
        for opened_input in input_models:
            if nreads != opened_input.data.shape[0]:
                raise ValueError("All input ramps must have the same number of reads.")
            ramp_arr.append(opened_input.data)
            dq_raw_arr.append(opened_input.dq_raw)
        ramp_arr = np.array(ramp_arr)
        dq_raw_arr = np.array(dq_raw_arr)

        _out = fit_gain_and_readnoise(
            delta_readtimes, ramp_arr, dq_raw_arr,
            _init_center_gain, _init_center_RN, _init_delta_gains, _init_delta_RNs,
            countratesidentical=self.countratesidentical,
            mode=self.mode, method=self.method, max_cores=self.max_cores
        )
        bestfit_gain, bestfit_rn, cov = _out

        # Output
        if self.mode == 'full_detector':
            bestfit_gain = np.full((ny,nx), bestfit_gain)
            bestfit_rn = np.full((ny,nx), bestfit_rn)
            cov = np.full((2,2,ny,nx), cov)
        output_gain.gain = bestfit_gain
        output_gain.rn = bestfit_rn
        output_gain.cov = cov
        output_gain.dq = np.zeros(bestfit_gain.shape, dtype=np.uint32)

        return output_gain

def fit_gain_and_readnoise(
    readtimes : np.ndarray, ramps : np.ndarray, dq_raw : np.ndarray,
    center_gains : np.ndarray, center_rns : np.ndarray,
    delta_gains: np.ndarray = None, delta_RNs : np.ndarray = None,
    countratesidentical: bool = False, mode : str = "per_pixel", method: str = 'quad',
    max_cores : int = 1,
):
    """
    Fit for the detector gain and/or read noise.

    Parameters
    ----------
    readtimes : np.ndarray
        1D array of read times.
    ramps : np.ndarray
        4D array of input rates. Size n_files x nreads x ny x nx.
    dq_raw : np.ndarray
        4D array of input UTR data quality flags. Size n_files x nreads x ny x nx.
    center_gains : np.ndarray | float
        Initial center guess for gain (e-/ADU).
    center_rns : np.ndarray | float
        Initial center guess for read noise (in DN).
    delta_gains : np.ndarray
        The grid sampling is defined as center_gains[i,j] + delta_gains for the maximum likelihood grid search.
        If None, only fit for read noise while fixing gain to this value.
        If method is 'quad', should be three elements [left, 0, right].
    delta_RNs : np.ndarray
        The grid sampling is defined as center_rns[i,j] + delta_RNs for the maximum likelihood grid search.
        If None, only fit for gain while fixing read noise to this value.
        If method is 'quad', should be three elements [left, 0, right].
    countratesidentical: bool
        If True, assume all ramps have identical count rates.
    mode : str
        'full_detector' to fit a single gain and read noise for the entire detector,
        'per_pixel' to fit gain and read noise for each pixel independently.
    method : str
        Method to use for fitting. Options are 'quad' for quadratic approximation, 'grid' for maximum likelihood grid search, 'both' for grid search followed by quadratic approximation.
    max_cores : int, optional
        Number of cores for parallelization. Default is 1 (no parallelization).
        Not used for mode == 'full_detector'.

    Returns
    -------
    gain : np.ndarray
        Best fit Gain (e-/ADU).
        Singleton if mode is 'full_detector', 2D array if mode is 'per_pixel'.
    rn : np.ndarray
        Best fit read noise (in DN).
        Singleton if mode is 'full_detector', 2D array if mode is 'per_pixel'.
    cov : np.ndarray
        Covariance matrix of the fit.
        2D matrix if mode is 'full_detector', 4D array if mode is 'per_pixel'.
    """

    if delta_gains is not None:
        if method == 'quad' and len(delta_gains) != 3:
            raise ValueError("In 'quad' method, delta_gains must have three elements: [left, 0, right]. Or be set to None.")
        elif (method == 'grid' or method == 'both') and len(delta_gains) < 4:
            raise ValueError("In 'grid' or 'both' method, delta_gains must have more than 3 elements.")
    if delta_RNs is not None:
        if method == 'quad' and len(delta_RNs) != 3:
            raise ValueError("In 'quad' method, delta_RNs must have three elements: [left, 0, right]. Or be set to None.")
        elif (method == 'grid' or method == 'both') and len(delta_RNs) < 4:
            raise ValueError("In 'grid' or 'both' method, delta_RNs must have more than 3 elements.")


    if mode.lower() == 'full_detector':
        C = fitramp_Brandt.Covar(readtimes)

        if isinstance(center_gains, np.ndarray):
            _center_gain = np.nanmedian(center_gains)
        else:
            _center_gain = center_gains
        if isinstance(center_rns, np.ndarray):
            _center_rn = np.nanmedian(center_rns)
        else:
            _center_rn = center_rns

        if delta_gains is not None:
            gains_init = _center_gain + delta_gains
        else:
            gains_init = np.array([_center_gain])
        if delta_RNs is not None:
            rns_init = _center_rn + delta_RNs
        else:
            rns_init = np.array([_center_rn])

        if method == 'quad':
            _out = _fit_single_gain_readnoise_quad_approx(readtimes, ramps, dq_raw, C,
                                                         gains_init, rns_init,
                                                         do_once=False, countratesidentical=countratesidentical)
        elif method == 'grid' or method == 'both':
            if method == 'grid':
                error_computation = 'posterior'
            elif method == 'both':
                error_computation = 'quad'
            _out = _fit_single_gain_readnoise(readtimes, ramps, dq_raw, C,
                                             gains_init, rns_init,
                                             error_computation=error_computation, countratesidentical=countratesidentical)

        bestfit_gain, bestfit_rn, cov = np.array([_out[0]]), np.array([_out[1]]), _out[2]

    elif mode.lower() == 'per_pixel':
        n_files, n_reads, ny,nx = ramps.shape

        if isinstance(center_gains, np.ndarray):
            _center_gains = center_gains
        elif isinstance(center_gains, float):
            _center_gains = np.full((ny,nx), center_gains)
        if isinstance(center_rns, np.ndarray):
            _center_rns = center_rns
        elif isinstance(center_rns, float):
            _center_rns = np.full((ny,nx), center_rns)

        _out = _fit_gain_and_readnoise_per_pixel(readtimes, ramps, dq_raw,
                                                _center_gains, _center_rns,
                                                delta_gains, delta_RNs,
                                                countratesidentical=countratesidentical,
                                                method= method,max_cores =max_cores)
        bestfit_gain, bestfit_rn, cov = _out

    return bestfit_gain, bestfit_rn, cov


def _fit_gain_and_readnoise_per_pixel(
    readtimes : np.ndarray, ramps : np.ndarray, dq_raw : np.ndarray,
    center_gains : np.ndarray, center_rns : np.ndarray,
    delta_gains: np.ndarray = None, delta_RNs : np.ndarray = None,
    countratesidentical: bool = False,  method: str = 'quad',
    max_cores : int = 1,
):
    """
    Fit the gain and read noise for each pixel on the detector using either quadratic approximation or maximum likelihood grid search.

    Parameters
    ----------
    readtimes : np.ndarray
        1D array of read times.
    ramps : np.ndarray
        2D array of input rates. Size n_files x nreads x ny x nx.
    dq_raw : np.ndarray
        2D array of input UTR data quality flags. Size n_files x nreads x ny x nx.
    center_gains : np.ndarray
        Initial center guess for gain (e-/ADU).
    center_rns : np.ndarray
        Initial center guess for read noise (in DN).
    delta_gains : np.ndarray
        The grid sampling is defined as center_gains[i,j] + delta_gains for the maximum likelihood grid search.
        If None, only fit for read noise while fixing gain to this value.
        If method is 'quad', should be three elements [left, 0, right].
    delta_RNs : np.ndarray
        The grid sampling is defined as center_rns[i,j] + delta_RNs for the maximum likelihood grid search.
        If None, only fit for gain while fixing read noise to this value.
        If method is 'quad', should be three elements [left, 0, right].
    countratesidentical: bool
        If True, assume all ramps have identical count rates.
    method : str
        Method to use for fitting. Options are 'quad' for quadratic approximation, 'grid' for maximum likelihood grid search, 'both' for grid search followed by quadratic approximation.
    max_cores : int, optional
        Number of cores for parallelization. Default is 1 (no parallelization).

    Returns
    -------
    gain : float
        Best fit Gain (e-/ADU)
    rn : float
        Best fit read noise (in DN)
    cov : np.ndarray
        Covariance matrix of the fit.
    """
    n_files, n_reads, ny, nx = ramps.shape

    if ramps.dtype is np.uint16:
        mp_data_type = ctypes.c_ushort
    else:
        mp_data_type = ctypes.c_float
    mp_float_type = ctypes.c_float
    mp_dq_raw_type = ctypes.c_uint8
    mp_dq_type = ctypes.c_uint
    types_tuple = (mp_data_type, mp_float_type, mp_dq_raw_type, mp_dq_type)

    gain_mp = RawArray(mp_float_type, nx * ny)
    gain_shape = (ny, nx)
    gain_np = _arraytonumpy(gain_mp, gain_shape, dtype=mp_float_type)
    gain_np[:] = np.zeros(gain_shape, dtype=np.float32)

    readnoise_mp = RawArray(mp_float_type, nx * ny)
    readnoise_shape = (ny, nx)
    readnoise_np = _arraytonumpy(readnoise_mp, readnoise_shape, dtype=mp_float_type)
    readnoise_np[:] = np.zeros(readnoise_shape, dtype=np.float32)

    cov_mp = RawArray(mp_float_type, 2 * 2 * nx * ny)
    cov_shape = (2,2,ny, nx)
    cov_np = _arraytonumpy(cov_mp, cov_shape, dtype=mp_float_type)
    cov_np[:] = np.zeros(cov_shape, dtype=np.float32)

    center_gains_mp = RawArray(mp_float_type, nx * ny)
    center_gains_shape = (ny, nx)
    center_gains_np = _arraytonumpy(center_gains_mp, center_gains_shape, dtype=mp_float_type)
    center_gains_np[:] = center_gains.astype(np.float32)

    center_rns_mp = RawArray(mp_float_type, nx * ny)
    center_rns_shape = (ny, nx)
    center_rns_np = _arraytonumpy(center_rns_mp, center_rns_shape, dtype=mp_float_type)
    center_rns_np[:] = center_rns.astype(np.float32)

    if max_cores > 1:
        ramps_mp = RawArray(mp_data_type, nx * ny * n_reads * n_files)
        ramps_shape = (n_files,n_reads, ny, nx)
        ramps_np = _arraytonumpy(ramps_mp, ramps_shape, dtype=mp_data_type)
        ramps_np[:] = ramps  # copy original array into shared array
        ramps = ramps_np  # free the original array from memory to avoid duplicates

        dq_raw_mp = RawArray(mp_dq_raw_type, nx * ny * n_reads * n_files)
        dq_raw_shape = (n_files,n_reads, ny, nx)
        dq_raw_np = _arraytonumpy(dq_raw_mp, dq_raw_shape, dtype=mp_dq_raw_type)
        if dq_raw is None:
            dq_raw_np[:] = np.zeros(dq_raw_np, dtype=np.uint8)
        else:
            dq_raw_np[:] = dq_raw  # copy original array into shared array
            dq_raw = dq_raw_np  # free the original array from memory to avoid duplicates


        # Prepare blocks
        block_size = max(1, ny // (4*max_cores)) if max_cores > 1 else ny

        _init_args = (
            ramps_mp, ramps_shape,
            dq_raw_mp, dq_raw_shape,
            gain_mp, gain_shape,
            readnoise_mp, readnoise_shape,
            cov_mp, cov_shape,
            center_gains_mp, center_gains_shape,
            center_rns_mp, center_rns_shape
        )

        ctx = mp.get_context("spawn")  # avoids unsafe fork after OpenMP init
        tpool = ctx.Pool(
            processes=max_cores,
            initializer=_tpool_init_fit_gain_readnoise,
            initargs=_init_args,
            maxtasksperchild=50
        )

        args_list = []
        for block_start in range(0, ny, block_size):
            block_end = min(block_start + block_size, ny)

            args = (block_start, block_end, readtimes,
                    delta_gains,delta_RNs,
                    countratesidentical, method, types_tuple)
            args_list.append(args)

        try:
            with numba_thread_scope(max_cores):
                tasks = [
                    tpool.apply_async(_fit_gain_and_readnoise_worker, args=(args_tuple,))
                    for args_tuple in args_list
                ]

            for t in tqdm(tasks, desc="Processing blocks"):
                t.wait()
        finally:
            tpool.close()
            tpool.join()
    else:
        # If not parallelizing, ie max_cores=1, just run directly without shared memory
        results = []

        for row_id in np.arange(ny):
            print(f"Fitting detector gain and/or readnoise: Processing row {row_id + 1} of {ny}.")
            args = (
                row_id,
                readtimes,
                ramps[:, :, [row_id], :],
                dq_raw[:, :, [row_id], :],
                center_gains_np[[row_id], :],
                center_rns_np[[row_id], :],
                delta_gains,delta_RNs,
                countratesidentical,
                method
            )

            results.append(_fit_gain_and_readnoise_row(args))

        for row_element in results:
            row_id, out_bestfit_gain, out_bestfit_rn, out_cov = row_element

            gain_np[row_id, :] = out_bestfit_gain
            readnoise_np[row_id, :] = out_bestfit_rn
            cov_np[:,:,row_id, :] = out_cov


    return gain_np, readnoise_np, cov_np


def _tpool_init_fit_gain_readnoise(
    data : np.ndarray, data_shape : tuple,
    dq_raw : np.ndarray, dq_raw_shape : tuple,
    gain : np.ndarray, gain_shape : tuple,
    readnoise : np.ndarray, readnoise_shape : tuple,
    cov : np.ndarray, cov_shape : tuple,
    center_gains : np.ndarray, center_gains_shape : tuple,
    center_rns : np.ndarray, center_rns_shape : tuple,
):
    """
    Initialize shared global variables for the multiprocessing pool.
    """

    global shared_data, shared_data_shape, \
        shared_dq_raw, shared_dq_raw_shape, \
        shared_gain, shared_gain_shape, \
        shared_readnoise, shared_readnoise_shape, \
        shared_cov, shared_cov_shape, \
        shared_center_gains, shared_center_gains_shape, \
        shared_center_rns, shared_center_rns_shape

    shared_data = data
    shared_data_shape = data_shape

    shared_dq_raw = dq_raw
    shared_dq_raw_shape = dq_raw_shape

    shared_gain = gain
    shared_gain_shape = gain_shape

    shared_readnoise = readnoise
    shared_readnoise_shape = readnoise_shape

    shared_cov = cov
    shared_cov_shape = cov_shape

    shared_center_gains = center_gains
    shared_center_gains_shape = center_gains_shape

    shared_center_rns = center_rns
    shared_center_rns_shape = center_rns_shape

def _fit_gain_and_readnoise_row(indata : tuple) -> tuple:
    """
    Helper function for parallelization fitting the gain and readnoise per detector row.
    """
    row_id, delta_readtimes, ramp_row, dq_raw_row, center_gains_row, center_rns_row, delta_gains,delta_RNs, countratesidentical,method  = indata
    n_files, n_reads, _, nx = ramp_row.shape
    # print(row_id, ramp_row.shape, ramp_row[0,:,0,0])

    C = fitramp_Brandt.Covar(delta_readtimes)

    if method == 'grid':
        error_computation = 'posterior'
    elif method == 'both':
        error_computation = 'quad'

    out_bestfit_gain = np.zeros((nx,), dtype=np.float32)
    out_bestfit_rn = np.zeros((nx,), dtype=np.float32)
    out_cov = np.zeros((2,2,nx), dtype=np.float32)

    for i in range(nx):
        if delta_gains is not None:
            gains_init = center_gains_row[0,i]+ delta_gains
        else:
            gains_init = np.array([center_gains_row[0,i]])
        if delta_RNs is not None:
            rns_init = center_rns_row[0,i]+delta_RNs
        else:
            rns_init = np.array([center_rns_row[0,i]])

        if method == 'quad':
            _out = _fit_single_gain_readnoise_quad_approx(delta_readtimes, ramp_row[:,:,0,i], dq_raw_row[:,:,0,i], C,
                                                         gains_init, rns_init,
                                                         do_once=False,countratesidentical=countratesidentical)
        elif method == 'grid' or method == 'both':
            _out = _fit_single_gain_readnoise(delta_readtimes, ramp_row[:,:,0,i], dq_raw_row[:,:,0,i], C,
                                             gains_init, rns_init,
                                             error_computation=error_computation,countratesidentical=countratesidentical)

        bestfit_gain, bestfit_rn, cov = _out

        out_bestfit_gain[i] = bestfit_gain
        out_bestfit_rn[i] = bestfit_rn
        out_cov[:,:,i] = cov

    return (row_id, out_bestfit_gain, out_bestfit_rn, out_cov)

def _fit_gain_and_readnoise_worker(args : tuple) -> tuple:
    """
    Worker function for multiprocessing. Runs _fit_gain_and_readnoise_row on a block of rows using shared arrays.

    Parameters
    ----------
    args : tuple
        Tuple containing: (block_start, block_end, delta_readtimes,delta_gains,delta_RNs, countratesidentical, method, types_tuple)

    Returns
    -------
    block_start : int
        Starting index of the block of rows processed.
    block_end : int
        Ending index of the block of rows processed.
    """
    block_start, block_end, delta_readtimes,delta_gains,delta_RNs, countratesidentical, method, types_tuple = args
    mp_data_type, mp_float_type, mp_dq_raw_type, mp_dq_type = types_tuple

    ramps_np = _arraytonumpy(shared_data, shared_data_shape, dtype=mp_data_type)
    dq_raw_np = _arraytonumpy(shared_dq_raw, shared_dq_raw_shape, dtype=mp_dq_raw_type)

    gain_np = _arraytonumpy(shared_gain, shared_gain_shape, dtype=mp_float_type)
    readnoise_np = _arraytonumpy(shared_readnoise, shared_readnoise_shape, dtype=mp_float_type)
    cov_np = _arraytonumpy(shared_cov, shared_cov_shape, dtype=mp_float_type)

    center_gains_np = _arraytonumpy(shared_center_gains, shared_center_gains_shape, dtype=mp_float_type)
    center_rns_np = _arraytonumpy(shared_center_rns, shared_center_rns_shape, dtype=mp_float_type)

    results = []
    for row_id in range(block_start, block_end):
        args_row = (
            row_id,
            delta_readtimes,
            ramps_np[:,:, [row_id], :],
            dq_raw_np[:,:, [row_id], :],
            center_gains_np[[row_id], :],
            center_rns_np[[row_id], :],
            delta_gains,delta_RNs,
            countratesidentical,
            method

        )
        results.append(_fit_gain_and_readnoise_row(args_row))

    for row_element in results:
        row_id, out_bestfit_gain, out_bestfit_rn, out_cov = row_element

        gain_np[row_id, :] = out_bestfit_gain
        readnoise_np[row_id, :] = out_bestfit_rn
        cov_np[:,:,row_id, :] = out_cov

    return (block_start, block_end)

def _fit_single_gain_readnoise_quad_approx(
    readtimes : np.ndarray, ramps : np.ndarray, dq_raw : np.ndarray, covar : fitramp_Brandt.Covar,
    gains_init : np.ndarray, rns_init : np.ndarray, do_once : bool = False,
        countratesidentical: bool = False
):
    """
    Fit the gain and read noise for each pixel on the detector using a quadratic approximation.
    The fit is actually performed twice to refine the best guess.
    The first iteration uses gains_init and rns_init.
    The second iteration recenters gains_init and rns_init around the best fit from the first iteration and use the covariance for scaling.

    Parameters
    ----------
    readtimes : np.ndarray
        1D array of read times.
    ramps : np.ndarray
        2D array of input rates. Size nramps x nreads (x ny x nx). 
        Extra y and x dimensions are flattened with nramps if they exist.
    dq_raw : np.ndarray
        2D array of input UTR data quality flags. Size nramps x nreads (x ny x nx).
        Extra y and x dimensions are flattened with nramps if they exist.
    covar : fitramp_Brandt.Covar class
           Should be appropriate for diffs_lin
    gains_init : np.ndarray
        Initial guess for gain (e-/ADU).
        Should be three elements (left, middle, right) with all gains_init > 0.
        Or if singleton, only fit for read noise while fixing gain to this value.
    rns_init : np.ndarray
        Initial guess for read noise (in DN).
        Should be three elements (left, middle, right) with all rns_init > 0.
        Or if singleton, only fit for gain while fixing read noise to this value.
    do_once : bool
        If True, perform the fit only once (no refinement).
    countratesidentical: bool
        If True, assume all ramps have identical count rates.

    Returns
    -------
    gain : float
        Best fit Gain (e-/ADU)
    rn : float
        Best fit read noise (in DN)
    cov : np.ndarray
        Covariance matrix of the fit.
    """
    nreads = readtimes.shape[0]
    _ramps = np.array(ramps).swapaxes(0, 1) # n_reads, n_files, ny, nx
    _dq_raw = np.array(dq_raw).swapaxes(0, 1) # n_reads, n_files, ny, nx
    _ramps = _ramps.reshape(nreads, -1)  # shape (n_reads, nfiles*ny*nx)
    _dq_raw = _dq_raw.reshape(nreads, -1)  # shape (n_reads, nfiles*ny*nx)
    
    y0 = 0
    diff_times = np.diff(readtimes)[:, None]
    diffs_lin = np.diff(_ramps, axis=0).astype(np.float64)/diff_times
    diffs_quad = np.diff((_ramps - y0) ** 2, axis=0).astype(np.float64)/diff_times

    n_reads,n_ramps = _dq_raw.shape
    mask = ((_dq_raw & DO_NOT_USE_FLAG_uint8) | (_dq_raw & SATURATED_FLAG_uint8)).astype(np.bool)
    mask2 = (_dq_raw & JUMP_DET_FLAG_uint8).astype(np.bool)
    diffs2use = ~(mask[1:n_reads] | mask[0:n_reads - 1] | mask2[1:n_reads])
    # diffs2use = np.full((n_reads-1,n_ramps),1,dtype=np.uint8)
    # diffs2use[5,:] = 0
    # diffs2use[10,:] = 0
    # diffs2use[20,:] = 0
    diffs2use = diffs2use.astype(np.uint8)

    # The quadratic form fit, followed by the maximum value that the quadratic
    # form takes and the maximum value seen on the dense grid.  Run the
    # quadratric form fit twice to make sure we get very close to the maximum
    # of the likelihood.
    if do_once:
        n_iter = 1
    else:
        n_iter = 2
    for i in range(n_iter):
        # three points each in read noise and gain to fit a quadratic form
        if i == 0:
            gains_short = gains_init.astype(np.float64)
            sigs_short = rns_init.astype(np.float64)
        else:
            if len(gains_short) > 1:
                bestfit_gain_err = np.sqrt(cov[0, 0])
                gains_short = [bestfit_gain- bestfit_gain_err,bestfit_gain, bestfit_gain + bestfit_gain_err]
            if len(sigs_short) > 1:
                bestfit_rn_err = np.sqrt(cov[1,1])
                sigs_short = [bestfit_rn- bestfit_rn_err,bestfit_rn, bestfit_rn + bestfit_rn_err]

        bestfit_gain, bestfit_rn, cov = _fitquad_gain_rn(diffs_lin, diffs_quad, covar,sigs_short, gains_short,
                                                        d2use=diffs2use,countratesidentical=countratesidentical)

    return bestfit_gain, bestfit_rn, cov


def _fitquad_gain_rn(
    diffs_lin,
    diffs_quad,
    covar,
    sigs_short,
    gains_short,
    d2use=None,
    countratesidentical=False,
):
    """
    Estimate best-fit (gain, read-noise) and an approximate covariance matrix.

    Logic:
      - If both grids have >1 point: call fit_gain_Brandt.fitquad(...)
      - If only sigs_short has 1 point: compute logL vs gain, fit a quadratic,
        take maximum at -b/(2a), and estimate sigma_gain ~ sqrt(-1/(2a)).
      - If only gains_short has 1 point: compute logL vs rn, fit a quadratic,
        take maximum at -b/(2a), and estimate sigma_rn ~ sqrt(-1/(2a)).

    Returns
    -------
    bestfit_gain : float
    bestfit_rn   : float
    cov          : (2,2) ndarray
        cov[0,0] ~ var_gain (as in your snippet), cov[1,1] ~ var_rn;
        off-diagonals are NaN unless fitquad returns something else.
    """

    if len(sigs_short) > 1 and len(gains_short) > 1:
        (bestfit_gain, bestfit_rn), cov, coefs = fit_gain_Brandt.fitquad(diffs_lin, diffs_quad, covar,
                                                sigs_short, gains_short, log=False,d2use=d2use,
                                                                         countratesidentical=countratesidentical)
    elif len(sigs_short) == 1:
        logL = fit_gain_Brandt.gen_likelihood_map(diffs_lin, diffs_quad, covar,
                                  sigs_short, gains_short, [0],
                                  countratesidentical=countratesidentical,d2use=d2use)
        a,b,c = _quad_1d_through_3pts(gains_short, logL[0,:,0])
        bestfit_gain = -b/(2*a)
        bestfit_rn = sigs_short[0]
        cov = np.full((2,2),np.nan)
        cov[0,0] = -1/(2*a)
    elif len(gains_short) == 1:
        logL = fit_gain_Brandt.gen_likelihood_map(diffs_lin, diffs_quad, covar,
                                  sigs_short, gains_short, [0],
                                  countratesidentical=countratesidentical,d2use=d2use)
        a,b,c = _quad_1d_through_3pts(sigs_short, logL[:,0,0])
        bestfit_gain = gains_short[0]
        bestfit_rn = -b/(2*a)
        cov = np.full((2,2),np.nan)
        cov[1,1] = -1/(2*a)

    return bestfit_gain, bestfit_rn, cov

def _fit_single_gain_readnoise(
        readtimes: np.ndarray, ramps: np.ndarray, dq_raw: np.ndarray, covar: fitramp_Brandt.Covar,
        gains_init: np.ndarray, rns_init: np.ndarray, error_computation: str = 'quad',
        countratesidentical: bool = False, return_likelihood: bool = False
):
    """
    Fit the gain and read noise using a grid search maximum likelihood.
    The grid search is defined by gains_init and rns_init.

    Parameters
    ----------
    readtimes : np.ndarray
        1D array of read times.
    ramps : np.ndarray
        2D array of input rates. Size nramps x nreads.
    dq_raw : np.ndarray
        2D array of input UTR data quality flags. Size nramps x nreads.
    covar : fitramp_Brandt.Covar class
           Should be appropriate for diffs_lin
    gains_init : np.ndarray
        Grid sampling for gain (e-/ADU). Elements should be all positive.
    rns_init : float
        Grid sampling for read noise (in DN). Elements should be all positive.
    error_computation : str
        Mode to compute the errors. Options are 'quad' for quadratic approximation, 'posterior' for posterior marginalization.
    countratesidentical: bool
        If True, assume all ramps have identical count rates.

    Returns
    -------
    gain : float
        Best fit Gain (e-/ADU)
    gain_err : float
        Best fit Gain error (e-/ADU)
    rn : float
        Best fit read noise (in DN)
    rn_err : float
        Best fit read noise error (in DN)
    """
    nreads = readtimes.shape[0]
    _ramps = np.array(ramps).swapaxes(0, 1) # n_reads, n_files, ny, nx
    _dq_raw = np.array(dq_raw).swapaxes(0, 1) # n_reads, n_files, ny, nx
    _ramps = _ramps.reshape(nreads, -1)  # shape (n_reads, nfiles *ny*nx)
    _dq_raw = _dq_raw.reshape(nreads, -1)  # shape (n_reads, nfiles*ny*nx)

    y0 = 0
    diff_times = np.diff(readtimes)[:, None]
    diffs_lin = np.diff(_ramps, axis=0).astype(np.float64)/diff_times
    diffs_quad = np.diff((_ramps - y0) ** 2, axis=0).astype(np.float64)/diff_times

    n_reads,n_ramps = _dq_raw.shape
    mask = ((_dq_raw & DO_NOT_USE_FLAG_uint8) | (_dq_raw & SATURATED_FLAG_uint8)).astype(np.bool)
    mask2 = (_dq_raw & JUMP_DET_FLAG_uint8).astype(np.bool)
    diffs2use = ~(mask[1:n_reads] | mask[0:n_reads - 1] | mask2[1:n_reads])
    # diffs2use = np.full((n_reads-1,n_ramps),1,dtype=np.uint8)
    # diffs2use[5,:] = 0
    # diffs2use[10,:] = 0
    # diffs2use[20,:] = 0
    diffs2use = diffs2use.astype(np.uint8)

    _rns_init = rns_init.astype(np.float64)
    _rns_init = _rns_init[_rns_init > 0]
    _gains_init = gains_init.astype(np.float64)
    _gains_init = _gains_init[_gains_init > 0]

    likelihoods = fit_gain_Brandt.gen_likelihood_map(diffs_lin, diffs_quad, covar, _rns_init, _gains_init, [0],
                                                     d2use=diffs2use,countratesidentical=countratesidentical)[..., 0]

    maxL = np.amax(likelihoods)
    k, l = np.unravel_index(np.argmax(likelihoods), likelihoods.shape)
    # bestfit_gain, bestfit_rn = _gains_init[l], rns_init[k]

    if error_computation == 'posterior':

        gain_post = np.sum(np.exp(likelihoods - np.amax(likelihoods)), axis=0)
        gain_post /= np.sum(gain_post)
        gains_init_diffs = np.diff(_gains_init, prepend=_gains_init[0] - (_gains_init[1] - _gains_init[0]))
        gain_post /= gains_init_diffs

        bestfit_gain, gain_left_error, gain_right_error = get_err_from_posterior(_gains_init, gain_post)
        bestfit_gain_err = np.max([gain_left_error, gain_right_error])

        if np.size(_rns_init) > 3:
            rn_post = np.sum(np.exp(likelihoods - np.amax(likelihoods)), axis=1)
            rn_post /= np.sum(rn_post)
            rns_init_diffs = np.diff(_rns_init, prepend=_rns_init[0] - (_rns_init[1] - _rns_init[0]))
            rn_post /= rns_init_diffs

            bestfit_rn, rn_left_error, rn_right_error = get_err_from_posterior(_rns_init, rn_post)
            bestfit_rn_err = np.max([rn_left_error, rn_right_error])
        else:
            bestfit_rn, bestfit_rn_err = np.nan, np.nan

        cov = np.full((2,2),np.nan)
        cov[0,0] = bestfit_gain_err
        cov[1,1] = bestfit_rn_err

        if return_likelihood:
            other_outputs = {}
            other_outputs["rns_init"] = _rns_init
            other_outputs["gains_init"] = _gains_init
            other_outputs["likelihoods"] = likelihoods
            return bestfit_gain, bestfit_rn, cov, other_outputs
        else:
            return bestfit_gain, bestfit_rn, cov

    elif error_computation == 'quad':
        # three points each in read noise and gain to fit a quadratic form
        n_iter = 2
        for i in range(n_iter):
            # three points each in read noise and gain to fit a quadratic form
            if i == 0:
                if len(_gains_init) > 1:
                    delta_gain = (_gains_init[1] - _gains_init[0])/2
                    gains_short = [_gains_init[l]-delta_gain,_gains_init[l], _gains_init[l]+delta_gain]
                else:
                    gains_short = _gains_init
                if len(_rns_init) > 1:
                    delta_rn = (_rns_init[1] - _rns_init[0])/2
                    sigs_short = [_rns_init[k]-delta_rn,_rns_init[k], _rns_init[k]+delta_rn]
                else:
                    sigs_short = _rns_init
            else:
                if len(gains_short) > 1:
                    bestfit_gain_err = np.sqrt(cov[0, 0])
                    gains_short = [bestfit_gain- bestfit_gain_err,bestfit_gain, bestfit_gain + bestfit_gain_err]
                if len(sigs_short) > 1:
                    bestfit_rn_err = np.sqrt(cov[1,1])
                    sigs_short = [bestfit_rn- bestfit_rn_err,bestfit_rn, bestfit_rn + bestfit_rn_err]

            bestfit_gain, bestfit_rn, cov = _fitquad_gain_rn(diffs_lin, diffs_quad, covar,sigs_short, gains_short,
                                                            d2use=diffs2use,countratesidentical=countratesidentical)

        return bestfit_gain, bestfit_rn, cov



def _quad_1d_through_3pts(x, y):
    """
    Fit y = a*x^2 + b*x + c through exactly three points (xi, yi),
    without explicit matrix inversion.

    x, y: array-like of length 3
    Returns: (a, b, c)
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if x.shape != (3,) or y.shape != (3,):
        raise ValueError("x and y must be length-3 arrays")
    if np.unique(x).size != 3:
        raise ValueError("x values must be distinct")

    x1, x2, x3 = x
    y1, y2, y3 = y

    d1 = (x1 - x2) * (x1 - x3)
    d2 = (x2 - x1) * (x2 - x3)
    d3 = (x3 - x1) * (x3 - x2)

    a = y1 / d1 + y2 / d2 + y3 / d3
    b = -(y1 * (x2 + x3) / d1 + y2 * (x1 + x3) / d2 + y3 * (x1 + x2) / d3)
    c = y1 * x2 * x3 / d1 + y2 * x1 * x3 / d2 + y3 * x1 * x2 / d3

    return a, b, c


# The following function come from
# https://github.com/oirlab/HISPEC_DRP/blob/jb-dev/hispecdrp/primitives/gain/make_gain_primitive.py
# def plot_2d_posterior(
#     likelihoods,
#     gains_init,
#     rns_init,
#     *,
#     aspect=0.4,
#     vmin=-20,
#     vmax=0,
#     cmap="bone_r",
#     contour_deltas=(11.8/2, 6.2/2, 2.3/2),
#     contour_color="r",
#     contour_lw=2,
#     cbar_label=r"$\log {\cal L}/{\cal L}_{\rm max}$",
#     xlabel=r"Gain ($e^-$/DN)",
#     ylabel=r"Read Noise (DN)",
#     title_2d=None,
#     title_1d=None,
#     show=False,
# ):
#     """
#     Plot a 2D log-likelihood map (shifted by max) with confidence contours,
#     and optionally a 1D marginalized gain posterior.

#     Parameters
#     ----------
#     likelihoods : (Nr, Ng) array
#         Log-likelihood values on the (rns_init, gains_init) grid.
#         Assumes axis-0 corresponds to rns_init and axis-1 corresponds to gains_init.
#     gains_init : (Ng,) array
#         Gain grid (x-axis).
#     rns_init : (Nr,) array
#         Read-noise grid (y-axis).
#     show : bool
#         If True, calls plt.show() at the end.

#     Returns
#     -------
#     figs : dict
#         {"2d": fig2d, "1d": fig1d_or_None}
#     axes : dict
#         {"2d": ax2d, "1d": ax1d_or_None}
#     """
#     likelihoods = np.asarray(likelihoods)
#     gains_init = np.asarray(gains_init)
#     rns_init = np.asarray(rns_init)

#     gain_post = np.sum(np.exp(likelihoods - np.amax(likelihoods)), axis=0)
#     gain_post /= np.sum(gain_post)
#     gains_init_diffs = np.diff(gains_init, prepend=gains_init[0] - (gains_init[1] - gains_init[0]))
#     gain_post /= gains_init_diffs

#     if likelihoods.ndim != 2:

#         raise ValueError("likelihoods must be 2D (Nr, Ng).")
#     if likelihoods.shape != (rns_init.size, gains_init.size):
#         raise ValueError(
#             f"Shape mismatch: likelihoods has shape {likelihoods.shape} but "
#             f"expected ({rns_init.size}, {gains_init.size}) = (len(rns_init), len(gains_init))."
#         )

#     maxL = np.nanmax(likelihoods)
#     extent = [gains_init[0], gains_init[-1], rns_init[0], rns_init[-1]]

#     # --- 2D figure ---
#     fig2d, ax2d = plt.subplots(figsize=(8, 6))
#     im = ax2d.imshow(
#         likelihoods - maxL,
#         origin="lower",
#         aspect=aspect,
#         extent=extent,
#         vmin=vmin,
#         vmax=vmax,
#         cmap=cmap,
#     )
#     cbar = fig2d.colorbar(im, ax=ax2d)
#     cbar.set_label(cbar_label)

#     ax2d.set_xlabel(xlabel)
#     ax2d.set_ylabel(ylabel)
#     if title_2d is not None:
#         ax2d.set_title(title_2d)

#     # Contours at maxL - delta
#     levels = [maxL - d for d in contour_deltas]
#     ax2d.contour(
#         likelihoods,
#         extent=extent,
#         levels=levels,
#         colors=[contour_color] * len(levels),
#         linewidths=[contour_lw] * len(levels),
#     )

#     gain_post = np.asarray(gain_post)
#     if gain_post.shape != (gains_init.size,):
#         raise ValueError(
#             f"gain_post has shape {gain_post.shape} but expected ({gains_init.size},)."
#         )
#     fig1d, ax1d = plt.subplots(figsize=(8, 6))
#     ax1d.plot(gains_init, gain_post, label="Full Numerical Marginalization")
#     ax1d.set_xlabel(xlabel)
#     ax1d.set_ylabel("Posterior (arb.)")
#     if title_1d is not None:
#         ax1d.set_title(title_1d)
#     ax1d.legend()

#     if show:
#         plt.show()

#     return {"2d": fig2d, "1d": fig1d}, {"2d": ax2d, "1d": ax1d}