from . import calc_nonlin_coeffs_Brandt as nonlin_Brandt
from ..stpipe.base_step import LigerIRISStep
from .. import datamodels
import numpy as np
import matplotlib.pyplot as plt
from typing import Sequence
from ..utils.stats import get_err_from_posterior
from ..datamodels.dqflags import DQ_FLAGS
from ..calibrations import GainSelector, ReadNoiseSelector, SaturationSelector, BiasSelector

import multiprocessing as mp
import ctypes
from ..utils.parallelization_utils import _arraytonumpy, numba_thread_scope
from multiprocessing.sharedctypes import RawArray
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)


__all__ = ['MakeNonLinStep','fit_nonlin_coefs']

SATURATED_FLAG_uint8 =  np.uint8(DQ_FLAGS["SATURATED"])
DO_NOT_USE_FLAG_uint8 = np.uint8(DQ_FLAGS["DO_NOT_USE"])
JUMP_DET_FLAG_uint8 = np.uint8(DQ_FLAGS["JUMP_DET"])

class MakeNonLinStep(LigerIRISStep):
    """
    This step computes the coefficients of a polynomial nonlinearity
    correction model from raw up-the-ramp (UTR) detector data

    Thresholds are also computed to characterize the onset and maximum extent
    of correctable nonlinearity (eg, 1% and 10% deviation from linearity).

    The step uses the algorithm described in Brandt (2025; PASP, 137, 125005). The fitted model
    characterizes the deviation of the measured signal from an ideal linear
    ramp and is intended to be applied later by the nonlinearity correction
    step. No science data are modified by this step; instead, a
    nonlinearity calibration model is produced.

    Use saturated flat fields to derive the nonlinearity correction model.

    The non-linearity correction is assumed to follow:
        
        P(DN) = a0 + a1*DN + a2*DN^2 + ... + an*DN^n
    
    where P(DN) is the corrected signal, DN is the measured signal, and
    a0, a1, ..., an are the polynomial coefficients derived in this step.
    Note that the ordering of the coefficients in the calibration file is from lowest
    order to highest order, which is the reverse of the usual numpy.polyval ordering.

    Polynomial fits may be carried out either in the standard power basis
    or in a Legendre polynomial basis. Reads that exceed a specified fraction
    of the saturation level are excluded from the fit.

    The fitting may be performed on a per-pixel basis or using a single
    model for the full detector. Although the full detector mode is only for
    testing since there are too many pixels on a normal detector and the
    matrix becomes too large with so many ramps.

    Parameters
    ----------
    input : list of str or list of RampModel
        List of input file paths or ramp models to process.
    max_cores : int, optional
        Maximum number of CPU cores to use.
        Default is 1.
    mode : {'per_pixel', 'channel', 'full_detector'}, optional
        Mode used to fit the nonlinearity parameters. ``'per_pixel'`` fits
        an independent model for each pixel. ``'full_detector'`` fits a
        single model to the entire detector. ``'channel'`` is reserved for
        future implementation.
    use_legendre : bool, optional
        If True, perform the polynomial fit using a Legendre polynomial
        basis. If False, use the standard power basis. Default is True.
    order : int, optional
        Order of the polynomial used to model the detector nonlinearity.
        Default is 5.
    readstart : int, optional
        Index (zero-based) of the first read to include in the fit. Default
        is 0.
    satval_frac : float, optional
        Fraction of the saturation level beyond which reads are excluded
        from the fit. Default is 0.95.
    criterion_for_nonlin_thresh : float, optional
        Fractional deviation from a linear ramp used to define the
        nonlinearity threshold, above which data are considered non-linear
        but still correctable. Default is 0.01.
    criterion_for_nonlin_max : float, optional
        Fractional deviation from a linear ramp used to define the maximum
        nonlinearity, above which data are considered too non-linear to be
        corrected accurately. Default is 0.05.

    Returns
    -------
    output : NonlinearCorrectionModel
        Nonlinearity correction calibration model containing the fitted
        polynomial coefficients and associated nonlinearity thresholds.

    References
    ----------
    Brandt, T. D. (2025), *A Classic Nonlinearity Correction Algorithm for
    Detectors Read Out Up-the-ramp*, PASP, 137, 125005.
    https://ui.adsabs.harvard.edu/abs/2025PASP..137l5005B/abstract

    Roman calibration pipeline reference:
    https://github.com/spacetelescope/romancal
    """

    spec = """
        max_cores = integer(default=1) # maximum number of CPU cores to use
        mode = string(default='per_pixel') # mode to fit the parameters. 'per_pixel' | 'channel' | 'full_detector'
        use_legendre = boolean(default=True) # fit in the Legendre polynomial basis?
        order = integer(default=5) # order of polynomial to fit for the nonlinearity correction
        readstart = integer(default=0) # first read (indexed from zero) that we use
        satval_frac = float(default=0.95) # fractional value of saturation beyond which reads are ignored.
        criterion_for_nonlin_thresh = float(default=0.01) # criterion to define the nonlinearity threshold.
        criterion_for_nonlin_max = float(default=0.05) # criterion to define the nonlinearity maximum.
        suffix = string(default='')
    """

    calibrations = {
        'gain' : {
            'selector' : GainSelector,
            'selector_kwargs' : {}
        },
        'rn' : {
            'selector' : ReadNoiseSelector,
            'selector_kwargs' : {}
        },
        'saturation' : {
            'selector' : SaturationSelector,
            'selector_kwargs' : {}
        },
        'bias' : {
            'selector' : BiasSelector,
            'selector_kwargs' : {}
        }
    }

    class_alias = 'make_nonlin'

    def process(self, input):
        if self.mode.lower() != 'full_detector' and self.mode.lower() != 'per_pixel':
            raise NotImplementedError(f"Only 'full_detector' and 'per_pixel' modes are implemented currently. Not {self.mode}")

        if self.mode.lower() == 'full_detector':
            logger.info(f"Running in full_detector mode. All detector pixels will be fitted jointly and a single gain and/or readnoise value will be returned for the entire chip.")
        elif self.mode.lower() == 'per_pixel':
            logger.info(f"Running in single_pixel mode. Each detector pixel will be fitted independently and a map of gain and/or readnoise will be returned.")


        if isinstance(input, (datamodels.LigerIRISDataModel, str)):
            _input_list_tmp = [input]
        if  isinstance(input, Sequence):
            _input_list_tmp = input
        nfiles = len(_input_list_tmp)
        logger.info(f"Deriving the detector non linearity polynomial coefficients from a list of {nfiles} inputs.")

        input_models = [datamodels.open(f) for f in _input_list_tmp]
        datamodel0 = input_models[0]
        nreads,ny,nx = datamodel0.data.shape

        gain, _ = self.get_calibration(datamodel0, 'gain')
        gain_model = self.open_model(gain)

        rn_cal, _ = self.get_calibration(datamodel0, 'rn')
        rn_model = self.open_model(rn_cal)

        # Get the saturation threshold model
        sat, _ = self.get_calibration(datamodel0, 'saturation')
        saturation_model = self.open_model(sat)

        # Get the bias model
        bias, _ = self.get_calibration(datamodel0, 'bias')
        bias_model = self.open_model(bias)

        # Define output model from inputs
        output_nonlin = datamodels.NonlinearCorrectionModel.from_datamodels(input_models)

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

        satval = self.satval_frac * (saturation_model.sat_thresh - bias_model.data)

        _out = fit_nonlin_coefs(
            ramp_arr, dq_raw_arr,
            gain_model.gain, rn_model.rn,
            order = self.order, satval = satval,
            mode = self.mode, use_legendre = self.use_legendre, readstart = self.readstart,
            criterion_for_nonlin_thresh = self.criterion_for_nonlin_thresh,
            criterion_for_nonlin_max = self.criterion_for_nonlin_max,
            max_cores =self.max_cores
        )
        nonlin_coeffs, nonlin_thresh,nonlin_max = _out

        # Output
        if self.mode == 'full_detector':
            nonlin_coeffs = np.broadcast_to(nonlin_coeffs[:, 0][:, None, None], (np.size(nonlin_coeffs), ny, nx))
            nonlin_thresh = np.full((ny,nx), nonlin_thresh)
            nonlin_max = np.full((ny,nx), nonlin_max)

        output_nonlin.coeffs = nonlin_coeffs
        output_nonlin.nonlin_thresh = nonlin_thresh # in DN
        output_nonlin.nonlin_max = nonlin_max # in DN
        output_nonlin.dq = np.zeros((ny, nx), dtype=np.uint32)

        return output_nonlin

def fit_nonlin_coefs(
    ramps : np.ndarray, dq_raw : np.ndarray, gain: np.ndarray, rn : np.ndarray,
    order : int = 5, satval : np.ndarray = None,
    mode : str = "per_pixel", use_legendre: bool = 'quad', readstart : int = 0,
    criterion_for_nonlin_thresh : float = 0.01, criterion_for_nonlin_max : float = 0.1,
    max_cores : int = 1,
):
    """
    Fit for the detector nonlinearity polynomial coefficients.

    Parameters
    ----------
    ramps : np.ndarray
        4D array of input rates. Size n_files x nreads x ny x nx.
    dq_raw : np.ndarray
        4D array of input UTR data quality flags. Size n_files x nreads x ny x nx.
    gain : np.ndarray
        gain map (ny,nx) (e-/ADU).
    rn : np.ndarray
        read noise map (ny,nx) (in DN).
    order : int = 5
        Order of polynomial to fit for the nonlinearity correction.
    satval : np.ndarray | None
        Map of values beyond which reads will be ignored in the fit (ny,nx) (in DN).
        Default is 64000
    mode : str
        'full_detector' to fit a single gain and read noise for the entire detector,
        'per_pixel' to fit gain and read noise for each pixel independently.
    use_legendre : bool
        If True, fit in the Legendre polynomial basis.
    readstart : int
        First read (indexed from zero) that we use.
    criterion_for_nonlin_thresh : float
        Criterion to define the nonlinearity threshold.
        ie, if the data DN deviates from a linear ramp by more than this fraction, it is considered non-linear, but it can be corrected reasonably accurately.
    criterion_for_nonlin_max : float
        Criterion to define the nonlinearity maximum.
        ie, if the data DN deviates from a linear ramp by more than this fraction, it is considered too non-linear and cannot be corrected accurately.
    max_cores : int, optional
        Number of cores for parallelization. Default is 1 (no parallelization).
        Not used for mode == 'full_detector'.

    Returns
    -------
    nonlin_coefs : np.ndarray
        Nonlinearity coefficients. Size (order+1, ny, nx) if mode is 'per_pixel', else (order+1,).
    nonlin_thresh : np.ndarray
        Nonlinearity threshold map (ny,nx) (in DN).
    nonlin_max : np.ndarray
        Nonlinearity maximum map (ny,nx) (in DN).
    """
    n_files, n_reads, ny, nx = ramps.shape

    if satval is None:
        satval = np.full((ny,nx), 64000)

    if mode.lower() == 'full_detector':

        row_id = 0
        ramp_row = np.array(ramps).swapaxes(1, 3) # n_files, ny, nx, n_reads
        dq_raw_row = np.array(dq_raw).swapaxes(1, 3) # n_files, ny, nx, n_reads
        ramp_row = ramp_row.reshape(n_files*ny*nx,n_reads)[:,:,np.newaxis]  # shape (nfiles*ny*nx,n_reads,1)
        dq_raw_row = dq_raw_row.reshape(n_files*ny*nx,n_reads)[:,:,np.newaxis]  # shape (nfiles*ny*nx,n_reads,1)
        gains_row = np.array([np.nanmedian(gain)])
        rns_row = np.array([np.nanmedian(rn)])
        satval_row = np.array([np.nanmedian(satval)])

        args = row_id, ramp_row, dq_raw_row, gains_row, rns_row, satval_row, order, use_legendre, readstart, criterion_for_nonlin_thresh, criterion_for_nonlin_max

        _out = _fit_nonlin_coefs_row(args)

        _,nonlin_coeffs, nonlin_thresh,nonlin_max = _out

    elif mode.lower() == 'per_pixel':
        n_files, n_reads, ny,nx = ramps.shape

        _out = _fit_nonlin_coefs_per_pixel(ramps, dq_raw,
                                            gain, rn,
                                            order = order, satval = satval,
                                            use_legendre = use_legendre, readstart = readstart,
                                            criterion_for_nonlin_thresh = criterion_for_nonlin_thresh,
                                            criterion_for_nonlin_max = criterion_for_nonlin_max,
                                          max_cores =max_cores)
        nonlin_coeffs, nonlin_thresh,nonlin_max = _out

    return nonlin_coeffs, nonlin_thresh,nonlin_max


def _fit_nonlin_coefs_per_pixel(
    ramps : np.ndarray, dq_raw : np.ndarray, gain: np.ndarray, rn : np.ndarray,
    order : int = 5, satval : np.ndarray = None,
    use_legendre: bool = 'quad', readstart : int = 0,
    criterion_for_nonlin_thresh : float = 0.01, criterion_for_nonlin_max : float = 0.1,
    max_cores : int = 1,
):
    """
    Fit for the nonlinearity polynomial coefficients on a per pixel basis.

    Parameters
    ----------
    ramps : np.ndarray
        4D array of input rates. Size n_files x nreads x ny x nx.
    dq_raw : np.ndarray
        4D array of input UTR data quality flags. Size n_files x nreads x ny x nx.
    gain : np.ndarray
        gain map (ny,nx) (e-/ADU).
    rn : np.ndarray
        read noise map (ny,nx) (in DN).
    order : int = 5
        Order of polynomial to fit for the nonlinearity correction.
    satval : np.ndarray | None
        Map of values beyond which reads will be ignored in the fit (ny,nx) (in DN).
        Default is 64000
    use_legendre : bool
        If True, fit in the Legendre polynomial basis.
    readstart : int
        First read (indexed from zero) that we use.
    criterion_for_nonlin_thresh : float
        Criterion to define the nonlinearity threshold.
        ie, if the data DN deviates from a linear ramp by more than this fraction, it is considered non-linear, but it can be corrected reasonably accurately.
    criterion_for_nonlin_max : float
        Criterion to define the nonlinearity maximum.
        ie, if the data DN deviates from a linear ramp by more than this fraction, it is considered too non-linear and cannot be corrected accurately.
    max_cores : int, optional
        Number of cores for parallelization. Default is 1 (no parallelization).

    Returns
    -------
    nonlin_coefs : np.ndarray
        Nonlinearity coefficients. Size (order+1, ny, nx).
    nonlin_thresh : np.ndarray
        Nonlinearity threshold map (ny,nx) (in DN).
    nonlin_max : np.ndarray
        Nonlinearity maximum map (ny,nx) (in DN).
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

    nonlin_coeffs_mp = RawArray(mp_float_type, (order+1)*nx * ny)
    nonlin_coeffs_shape = ((order+1), ny, nx)
    nonlin_coeffs_np = _arraytonumpy(nonlin_coeffs_mp, nonlin_coeffs_shape, dtype=mp_float_type)
    nonlin_coeffs_np[:] = np.zeros(nonlin_coeffs_shape, dtype=np.float32)

    nonlin_thresh_mp = RawArray(mp_float_type, nx * ny)
    nonlin_thresh_shape = (ny, nx)
    nonlin_thresh_np = _arraytonumpy(nonlin_thresh_mp, nonlin_thresh_shape, dtype=mp_float_type)
    nonlin_thresh_np[:] = np.zeros(nonlin_thresh_shape, dtype=np.float32)

    nonlin_max_mp = RawArray(mp_float_type, nx * ny)
    nonlin_max_shape = (ny, nx)
    nonlin_max_np = _arraytonumpy(nonlin_max_mp, nonlin_max_shape, dtype=mp_float_type)
    nonlin_max_np[:] = np.zeros(nonlin_max_shape, dtype=np.float32)

    gains_mp = RawArray(mp_float_type, nx * ny)
    gains_shape = (ny, nx)
    gains_np = _arraytonumpy(gains_mp, gains_shape, dtype=mp_float_type)
    gains_np[:] = gain.astype(np.float32)

    rns_mp = RawArray(mp_float_type, nx * ny)
    rns_shape = (ny, nx)
    rns_np = _arraytonumpy(rns_mp, rns_shape, dtype=mp_float_type)
    rns_np[:] = rn.astype(np.float32)

    satval_mp = RawArray(mp_float_type, nx * ny)
    satval_shape = (ny, nx)
    satval_np = _arraytonumpy(satval_mp, satval_shape, dtype=mp_float_type)
    satval_np[:] = satval.astype(np.float32)

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
            nonlin_coeffs_mp, nonlin_coeffs_shape,
            nonlin_thresh_mp, nonlin_thresh_shape,
            nonlin_max_mp, nonlin_max_shape,
            gains_mp, gains_shape,
            rns_mp, rns_shape,
            satval_mp, satval_shape,
        )

        ctx = mp.get_context("spawn")  # avoids unsafe fork after OpenMP init
        tpool = ctx.Pool(
            processes=max_cores,
            initializer=_tpool_init_fit_nonlin_coefs,
            initargs=_init_args,
            maxtasksperchild=50
        )

        args_list = []
        for block_start in range(0, ny, block_size):
            block_end = min(block_start + block_size, ny)

            args = (block_start, block_end, order,use_legendre,readstart,criterion_for_nonlin_thresh,criterion_for_nonlin_max, types_tuple)
            args_list.append(args)

        try:
            with numba_thread_scope(max_cores):
                tasks = [
                    tpool.apply_async(_fit_nonlin_coefs_worker, args=(args_tuple,))
                    for args_tuple in args_list
                ]

            for t in tqdm(tasks, desc="Processing blocks nonlin coefs fitting"):
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
                ramps[:, :, row_id, :],
                dq_raw[:, :, row_id, :],
                gains_np[row_id, :],
                rns_np[row_id, :],
                satval_np[row_id, :],
                order,
                use_legendre,
                readstart,
                criterion_for_nonlin_thresh,
                criterion_for_nonlin_max
            )

            results.append(_fit_nonlin_coefs_row(args))

        for row_element in results:
            row_id, nonlin_coeffs, nonlin_thresh,nonlin_max = row_element

            nonlin_coeffs_np[:,row_id, :] = nonlin_coeffs
            nonlin_thresh_np[row_id, :] = nonlin_thresh
            nonlin_max_np[row_id, :] = nonlin_max

    return nonlin_coeffs_np, nonlin_thresh_np,nonlin_max_np


def _tpool_init_fit_nonlin_coefs(
    data : np.ndarray, data_shape : tuple,
    dq_raw : np.ndarray, dq_raw_shape : tuple,
    nonlin_coeffs : np.ndarray, nonlin_coeffs_shape : tuple,
    nonlin_thresh : np.ndarray, nonlin_thresh_shape : tuple,
    nonlin_max : np.ndarray, nonlin_max_shape : tuple,
    gains : np.ndarray, gains_shape : tuple,
    rns : np.ndarray, rns_shape : tuple,
    satval : np.ndarray, satval_shape : tuple,
):
    """
    Initialize shared global variables for the multiprocessing pool.
    """

    global shared_data, shared_data_shape, \
        shared_dq_raw, shared_dq_raw_shape, \
        shared_nonlin_coeffs, shared_nonlin_coeffs_shape, \
        shared_nonlin_thresh, shared_nonlin_thresh_shape, \
        shared_nonlin_max, shared_nonlin_max_shape, \
        shared_gains, shared_gains_shape, \
        shared_rns, shared_rns_shape, \
        shared_satval, shared_satval_shape

    shared_data = data
    shared_data_shape = data_shape

    shared_dq_raw = dq_raw
    shared_dq_raw_shape = dq_raw_shape

    shared_nonlin_coeffs = nonlin_coeffs
    shared_nonlin_coeffs_shape = nonlin_coeffs_shape

    shared_nonlin_thresh = nonlin_thresh
    shared_nonlin_thresh_shape = nonlin_thresh_shape

    shared_nonlin_max = nonlin_max
    shared_nonlin_max_shape = nonlin_max_shape

    shared_gains = gains
    shared_gains_shape = gains_shape

    shared_rns = rns
    shared_rns_shape = rns_shape

    shared_satval = satval
    shared_satval_shape = satval_shape

def _fit_nonlin_coefs_row(indata : tuple) -> tuple:
    """
    Helper function for parallelization fitting the gain and readnoise per detector row.
    """
    row_id, ramp_row, dq_raw_row, gains_row, rns_row,satval_row, order,use_legendre,readstart,criterion_for_nonlin_thresh,criterion_for_nonlin_max  = indata
    n_files, n_reads, nx = ramp_row.shape

    # ramp_row should be (n_files, n_reads, nx)
    _ramps = ramp_row[:, readstart:, :]
    pedestal = np.nanmedian(_ramps[:,0,:],axis=0)

    n_files, n_reads,n_ramps = dq_raw_row.shape
    mask = ((dq_raw_row & DO_NOT_USE_FLAG_uint8) | (dq_raw_row & SATURATED_FLAG_uint8)).astype(np.bool)
    mask2 = (dq_raw_row & JUMP_DET_FLAG_uint8).astype(np.bool)
    diffs2use = ~(mask[:, 1:n_reads,:] | mask[:, 0:n_reads - 1,:] | mask2[:, 1:n_reads,:])
    diffs2use = diffs2use.astype(np.uint8)

    res = nonlin_Brandt.get_nonlin_coefs(_ramps, rns_row, gains_row, order, pedestal,satval=satval_row, d2u_list=diffs2use,use_legendre=use_legendre)

    res = nonlin_Brandt.get_nonlin_coefs(_ramps, rns_row, gains_row, order, pedestal,satval=satval_row, d2u_list=diffs2use,use_legendre=use_legendre,
                                         last_pars=res)

    nonlin_coefs = res.nonlin_coefs.T # N_coeffs x nx
    nonlin_coefs =np.insert(nonlin_coefs, 0, np.zeros((nx,)),axis=0) # add zero-th order term

    # figure out nonlin_thresh,nonlin_max
    nonlin_thresh = _find_first_valid_root_batch(nonlin_coefs[::-1,:],  criterion_for_nonlin_thresh,satval=satval_row)
    nonlin_max = _find_first_valid_root_batch(nonlin_coefs[::-1,:],  criterion_for_nonlin_max,satval=satval_row)

    return (row_id, nonlin_coefs, nonlin_thresh,nonlin_max)

def _fit_nonlin_coefs_worker(args : tuple) -> tuple:
    """
    Worker function for multiprocessing. Runs _fit_nonlin_coefs_row on a block of rows using shared arrays.

    Parameters
    ----------
    args : tuple
        Tuple containing: (block_start, block_end, order,use_legendre,readstart,criterion_for_nonlin_thresh,criterion_for_nonlin_max, types_tuple)

    Returns
    -------
    block_start : int
        Starting index of the block of rows processed.
    block_end : int
        Ending index of the block of rows processed.
    """
    block_start, block_end, order,use_legendre,readstart,criterion_for_nonlin_thresh,criterion_for_nonlin_max, types_tuple = args
    mp_data_type, mp_float_type, mp_dq_raw_type, mp_dq_type = types_tuple

    ramps_np = _arraytonumpy(shared_data, shared_data_shape, dtype=mp_data_type)
    dq_raw_np = _arraytonumpy(shared_dq_raw, shared_dq_raw_shape, dtype=mp_dq_raw_type)

    nonlin_coeffs_np = _arraytonumpy(shared_nonlin_coeffs, shared_nonlin_coeffs_shape, dtype=mp_float_type)
    nonlin_thresh_np = _arraytonumpy(shared_nonlin_thresh, shared_nonlin_thresh_shape, dtype=mp_float_type)
    nonlin_max_np = _arraytonumpy(shared_nonlin_max, shared_nonlin_max_shape, dtype=mp_float_type)

    gains_np = _arraytonumpy(shared_gains, shared_gains_shape, dtype=mp_float_type)
    rns_np = _arraytonumpy(shared_rns, shared_rns_shape, dtype=mp_float_type)
    satval_np = _arraytonumpy(shared_satval, shared_satval_shape, dtype=mp_float_type)

    results = []
    for row_id in range(block_start, block_end):
        args_row = (
                row_id,
                ramps_np[:, :, row_id, :],
                dq_raw_np[:, :, row_id, :],
                gains_np[row_id, :],
                rns_np[row_id, :],
                satval_np[row_id, :],
                order,
                use_legendre,
                readstart,
                criterion_for_nonlin_thresh,
                criterion_for_nonlin_max
        )
        results.append(_fit_nonlin_coefs_row(args_row))

    for row_element in results:
        row_id, nonlin_coeffs, nonlin_thresh,nonlin_max = row_element

        nonlin_coeffs_np[:,row_id, :] = nonlin_coeffs
        nonlin_thresh_np[row_id, :] = nonlin_thresh
        nonlin_max_np[row_id, :] = nonlin_max

    return (block_start, block_end)


def _find_first_valid_root_batch(
    nonlin_correction_coefs,
    my_threshold=0.01,
    satval=np.iinfo(np.uint16).max,
    min_root=1,
    atol=1e-10,
):
    """
    Batch-solve for the smallest admissible real root x, independently for each column ix,
    where the polynomial P_ix(x) is defined by coefficients in ``nonlin_correction_coefs[:, ix]``
    (NumPy / ``np.polyval`` convention: highest degree first), and x satisfies:

        (P_ix(x) - x) / x = my_threshold

    This is equivalent to solving, for each ix:

        P_ix(x) - (1 + my_threshold) * x = 0

    and selecting the smallest real root in (min_root[ix], satval[ix]].

    Parameters
    ----------
    nonlin_correction_coefs : array_like
        2D array of shape (n_coeffs, nx). Column ix contains the polynomial coefficients
        for P_ix(x), ordered from highest degree to constant term.
    satval : float or array_like, optional
        Upper bound(s) on acceptable roots. Either a scalar or a 1D array of length nx.
        Default is max uint16.
    min_root : float or array_like, optional
        Strict lower bound(s) on acceptable roots. Either a scalar or a 1D array of length nx.
        Default is 1.
    my_threshold : float, optional
        Threshold T in the equation (P(x) - x)/x = T. Default is 0.01.
    atol : float, optional
        Absolute tolerance for deciding whether a root is (numerically) real.
        Default is 1e-10.

    Returns
    -------
    root0 : ndarray
        1D float array of shape (nx,). Each element is the smallest admissible real root
        for that column, or NaN if no admissible root exists (or if the polynomial is invalid).

    Notes
    -----
    - Uses ``np.roots`` per column; there is no true vectorized root-finding in NumPy.
    - If the polynomial degree is < 1 (i.e., no linear term), that column returns NaN.
    """
    coefs = np.asarray(nonlin_correction_coefs, dtype=float)
    if coefs.ndim != 2:
        raise ValueError("nonlin_correction_coefs must be 2D with shape (n_coeffs, nx).")

    n_coeffs, nx = coefs.shape
    if n_coeffs < 2:
        # No linear term exists, cannot subtract (1+T)*x robustly
        return np.full(nx, np.nan, dtype=float)

    # Broadcast satval/min_root to per-column arrays
    sat_arr = np.asarray(satval, dtype=float)
    min_arr = np.asarray(min_root, dtype=float)

    if sat_arr.ndim == 0:
        sat_arr = np.full(nx, float(sat_arr), dtype=float)
    if min_arr.ndim == 0:
        min_arr = np.full(nx, float(min_arr), dtype=float)

    if sat_arr.shape != (nx,):
        raise ValueError(f"satval must be a scalar or shape (nx,), got {sat_arr.shape}.")
    if min_arr.shape != (nx,):
        raise ValueError(f"min_root must be a scalar or shape (nx,), got {min_arr.shape}.")

    out = np.full(nx, np.nan, dtype=float)

    for ix in range(nx):
        # Build Q(x) = P(x) - (1+T)*x
        tmp = coefs[:, ix].copy()
        tmp[-2] -= (1.0 + my_threshold)

        # If leading coefficients are zero, np.roots can behave poorly; trim them
        # (while preserving at least degree-1 if possible).
        nz = np.flatnonzero(tmp)
        if nz.size == 0:
            continue
        first_nz = nz[0]
        tmp_trim = tmp[first_nz:]

        # Need at least a linear polynomial after trimming
        if tmp_trim.size < 2:
            continue

        roots = np.roots(tmp_trim)

        # Keep (numerically) real roots
        real_roots = roots[np.isclose(roots.imag, 0.0, atol=atol)].real
        if real_roots.size == 0:
            continue

        # Enforce bounds: (min_root, satval]
        valid = real_roots[(real_roots > min_arr[ix]) & (real_roots <= sat_arr[ix])]
        if valid.size == 0:
            continue

        out[ix] = np.min(valid)

    return out