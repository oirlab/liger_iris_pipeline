import numpy as np

from stcal.ramp_fitting import ramp_fit
from stcal.ramp_fitting.ramp_fit_class import RampData

import multiprocessing as mp
import ctypes
from ..utils.parallelization_utils import _arraytonumpy, numba_thread_scope
from multiprocessing.sharedctypes import RawArray

from ..datamodels.dqflags import DQ_FLAGS
from .ramp_fit_utils import get_mid_delta_times
from ..jump_detection.jump_detection_jwst_old import _jump_detection_jwst_row

from . import fitramp_Brandt
from . import fitramp_cython_Brandt as fitramp_cython

from tqdm import tqdm

__all__ = ['fit_ramps_jwst']

SATURATED_FLAG = DQ_FLAGS["SATURATED"]
DO_NOT_USE_FLAG = DQ_FLAGS["DO_NOT_USE"]
JUMP_DET_FLAG = DQ_FLAGS["JUMP_DET"]
SATURATED_FLAG_uint8 =  np.uint8(DQ_FLAGS["SATURATED"])
DO_NOT_USE_FLAG_uint8 = np.uint8(DQ_FLAGS["DO_NOT_USE"])
JUMP_DET_FLAG_uint8 = np.uint8(DQ_FLAGS["JUMP_DET"])


def _fit_ramps_cython_row(indata: tuple) -> tuple:
    """
    Passes data for each row of a ramp to Tim Brandt's likelihood-based ramp fitting algorithm in Cython.

    Parameters
    ----------
    indata : Tuple[int, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, str]
        Tuple containing the following elements:
            ramp row index (int)
            read times (np.ndarray)
            ramp data (np.ndarray)
            readnoise (np.ndarray)
            gain (np.ndarray)
            DQ cube (np.ndarray)
            DQ image (np.ndarray)
            dark current (np.ndarray)
            algorithm (str)

    Returns
    -------
    i : int
        Index of input row from the ramps, same as input.
    slope : np.ndarray
        Slope image (1, nx).
    dq_out : np.ndarray
        Output data quality image with flags from algorithm (1, nx).
    var_poisson : np.ndarray
        Output variance from poisson noise (1, nx).
    var_rnoise : np.ndarray
        Output variance from read noise (1, nx).
    err : np.ndarray
        Output error in slope image (1, nx).
    """

    i, readtimes, data_3d, readnoise_2d, gain_2d, groupdq, pixeldq_2d, dark_current_2d, algorithm = indata

    # We are implicitly fitting by row, so columns is only other axis and nrows=1
    nints, n_reads, ny, nx = data_3d.shape

    _ramps = data_3d[0, :, 0,:]
    _dq_raw = groupdq[0, :, 0,:]

    y0 = 0
    diff_times = np.diff(readtimes)[:, None]
    diffs = np.diff(_ramps, axis=0).astype(np.float64) / diff_times
    n0, n1 = diffs.shape

    n_reads,n_ramps = _dq_raw.shape
    mask = ((_dq_raw & DO_NOT_USE_FLAG_uint8) | (_dq_raw & SATURATED_FLAG_uint8)).astype(np.bool)
    mask2 = (_dq_raw & JUMP_DET_FLAG_uint8).astype(np.bool)
    diffs2use = ~(mask[1:n_reads] | mask[0:n_reads - 1] | mask2[1:n_reads])
    diffs2use = diffs2use.astype(np.uint8)

    # todo: try to put covar in shared memory?
    covar = fitramp_Brandt.Covar(readtimes.astype(np.float64))

    cguess = np.sum(diffs*diffs2use, axis=0)
    cguess /= np.sum(diffs2use, axis=0)
    cguess *= cguess > 0

    cython_out = fitramp_cython.fit_ramps_row(
        diffs, diffs2use,
        covar.alpha_phnoise, covar.beta_phnoise,
        covar.alpha_readnoise, covar.beta_readnoise,
        readnoise_2d[0,:].astype(np.float64),gain_2d[0,:].astype(np.float64), cguess, n1, n0)
    logdetC_np, A_np, B_np, C_np, countrate_np, chisq_np, uncert_np = cython_out

    var_poisson = np.full((1, nx),np.nan)
    var_rnoise = np.full((1, nx),np.nan)
    dq = np.zeros((1, nx), dtype=np.uint32)

    return dict(
        i = i,
        slope = countrate_np.astype(np.float32),
        dq = dq.astype(np.uint32),
        var_poisson = var_poisson.astype(np.float32),
        var_rnoise = var_rnoise.astype(np.float32),
        err = uncert_np.astype(np.float32)
    )

    #return (i, countrate_np, dq, var_poisson, var_rnoise, uncert_np)


def _fit_ramps_jwst_row(indata : tuple) -> tuple:
    """
    Passes data for each row of a ramp to stcal.ramp_fitting.likely_fit algorithms.

    Parameters
    ----------
    indata : Tuple[int, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, str]
        Tuple containing the following elements:
            ramp row index (int)
            read times (np.ndarray)
            ramp data (np.ndarray)
            readnoise (np.ndarray)
            gain (np.ndarray)
            DQ cube (np.ndarray)
            DQ image (np.ndarray)
            dark current (np.ndarray)
            algorithm (str)
     
    Returns
    -------
    i : int
        Index of input row from the ramps, same as input.
    slope : np.ndarray
        Slope image (1, nx).
    dq_out : np.ndarray
        Output data quality image with flags from algorithm (1, nx).
    var_poisson : np.ndarray
        Output variance from poisson noise (1, nx).
    var_rnoise : np.ndarray
        Output variance from read noise (1, nx).
    err : np.ndarray
        Output error in slope image (1, nx).
    """

    i, times, data_3d, readnoise_2d, gain_2d, groupdq, pixeldq_2d, dark_current_2d, algorithm = indata

    # We are implicitly fitting by row, so columns is only other axis and nrows=1
    nints, nframes, ny, nx = data_3d.shape

    # Set static parameters for stcal.ramp_fitting algorithms
    save_opt = False # Save optional output
    weighting = "optimal"
    suppress_one_group = False # Suppress saturated ramps with good 0th group

    # Initialize ramp data model
    ramp_data = RampData()

    # Explicitly set flags required by JWST pipeline
    ramp_data.flags_do_not_use = DQ_FLAGS['DO_NOT_USE']
    ramp_data.flags_jump_det = DQ_FLAGS['JUMP_DET']
    ramp_data.flags_saturated = DQ_FLAGS['SATURATED']
    ramp_data.flags_no_gain_val = DQ_FLAGS['UNRELIABLE_FLAT'] # Check if this is best/optimal flag
    ramp_data.flags_unreliable_slope = DQ_FLAGS['UNRELIABLE_SLOPE']
    ramp_data.flags_chargeloss = DQ_FLAGS['OUTLIER'] # Check if this is best/optimal flag - only required by FIXSEN_C

    # Explicitly set data arrays
    ramp_data.data = data_3d
    ramp_data.groupdq = groupdq
    ramp_data.pixeldq = pixeldq_2d
    ramp_data.average_dark_current = dark_current_2d

    # Get average exposure time
    diffs = [times[i+1] - times[i] for i in range(len(times)-1)]
    group_time = np.average(diffs)

    # Set other required parameters
    ramp_data.algorithm = algorithm
    ramp_data.start_row = 0
    ramp_data.num_rows = ny
    ramp_data.nframes = 1 # this corresponds to nints instead of nframes as above

    # Required by FIXSEN_C for frame time
    ramp_data.frame_time = 0.0
    ramp_data.group_time = group_time
    ramp_data.groupgap = 0
    ramp_data.drop_frames1 = 0

    ramp_data.suppress_one_group_ramps = suppress_one_group

    # Times information is set as read_pattern parameter of RampData
    ramp_data.read_pattern = list(times)

    #todo: we are disabling the jump detection for now, because we cannot get the group DQ flags to return from the function.
    # and we might need it to estimate the mid_time correctly.
    ramp_data.rejection_threshold = np.inf

    # Run ramp fitting
    if algorithm == 'LIKELY':
        if nframes < ramp_fit.likely_fit.LIKELY_MIN_NGROUPS:
            raise Exception(f'Input ramps have {nframes} frames which is less than LIKELY algorithm requirement of {ramp_fit.likely_fit.LIKELY_MIN_NGROUPS} frames')
        # Call directly to likely ramp fit code
        image_info, integ_info, opt_info = ramp_fit.likely_fit.likely_ramp_fit(
            ramp_data, readnoise_2d, gain_2d
        )
    elif algorithm == 'FIXSEN_C':
        # Call to C extension for FIXSEN slope fitting
        image_info, _, _ = ramp_fit.ols_fit.ols_slope_fitter(
            ramp_data, gain_2d, readnoise_2d, weighting, save_opt)

    # Return results
    return dict(
        i = i,
        **image_info
    )

def _fit_ramps_worker(args : tuple) -> tuple:
    """
    Worker function for multiprocessing. Runs _fit_ramps_jwst_row on a block of rows using shared arrays.

    Parameters
    ----------
    args : tuple
        (block_start, block_end, times, algorithm, types_tuple)
    
    Returns
    -------
    block_start : int
        Starting index of the block of rows processed.
    block_end : int
        Ending index of the block of rows processed.
    results : list
        List of results from processing each row in the block.
    """
    block_start, block_end, times, algorithm, types_tuple = args
    mp_data_type, mp_float_type, mp_dq_raw_type, mp_dq_type = types_tuple

    ramps_np = _arraytonumpy(shared_data, shared_data_shape, dtype=mp_data_type)
    dq_raw_np = _arraytonumpy(shared_dq_raw, shared_dq_raw_shape, dtype=mp_dq_raw_type)
    dq_image_np = _arraytonumpy(shared_dq_image, shared_dq_image_shape, dtype=mp_dq_type)
    gain_np = _arraytonumpy(shared_gain, shared_gain_shape, dtype=mp_float_type)
    dark_np = _arraytonumpy(shared_dark, shared_dark_shape, dtype=mp_float_type)
    rdnoise_np = _arraytonumpy(shared_read_noise, shared_read_noise_shape, dtype=mp_float_type)
    start_times_np = _arraytonumpy(shared_start_times, shared_start_times_shape, dtype=mp_float_type)

    slope_image_np = _arraytonumpy(shared_slope_image, shared_slope_image_shape, dtype=mp_float_type)
    slope_errors_np = _arraytonumpy(shared_slope_errors, shared_slope_errors_shape, dtype=mp_float_type)
    var_poisson_image_np = _arraytonumpy(shared_var_poisson_image, shared_var_poisson_image_shape, dtype=mp_float_type)
    var_rnoise_image_np = _arraytonumpy(shared_var_rnoise_image, shared_var_rnoise_image_shape, dtype=mp_float_type)
    mid_times_np = _arraytonumpy(shared_mid_times, shared_mid_times_shape, dtype=mp_float_type)

    results = []
    for row in range(block_start, block_end):
        args_row = (
            row,
            times,
            ramps_np[np.newaxis,:, [row], :],
            rdnoise_np[[row], :],
            gain_np[[row], :],
            dq_raw_np[np.newaxis,:, [row], :],
            dq_image_np[[row], :],
            dark_np[[row], :],
            algorithm
        )
        if algorithm == 'CYTHON_LIKELY':
            results.append(_fit_ramps_cython_row(args_row))
        else:
            results.append(_fit_ramps_jwst_row(args_row))

    for row_element in results:

        row = row_element['i']
        slope_image_np[row, :] = row_element['slope']
        slope_errors_np[row, :] = row_element['err']
        dq_image_np[row, :] = dq_image_np[row, :] | row_element['dq'][0]
        var_poisson_image_np[row, :] = row_element['var_poisson']
        var_rnoise_image_np[row, :] = row_element['var_rnoise']

    mid_times_np[block_start:block_end, :] = start_times_np[block_start:block_end, :] +\
                                             get_mid_delta_times(times, dq_raw_np[:, block_start:block_end, :])

    _dq_raw = dq_raw_np[:, block_start:block_end, :] - (dq_raw_np[:, block_start:block_end, :] & DO_NOT_USE_FLAG_uint8)
    dq_image_np[block_start:block_end, :] |= np.bitwise_or.reduce(_dq_raw)

    return (block_start, block_end)

def _jump_detection_worker(args : tuple) -> tuple:
    """
    Worker function for multiprocessing. Runs _jump_detection_worker on a block of rows using shared arrays.

    Parameters
    ----------
    args : tuple
        Tuple containing: (block_start, block_end, times, algorithm, types_tuple)

    Returns
    -------
    tuple
        (block_start, block_end)
    """
    block_start, block_end, times, rejection_threshold, types_tuple = args
    mp_data_type, mp_float_type, mp_dq_raw_type, mp_dq_type = types_tuple

    ramps_np = _arraytonumpy(shared_data, shared_data_shape, dtype=mp_data_type)
    dq_raw_np = _arraytonumpy(shared_dq_raw, shared_dq_raw_shape, dtype=mp_dq_raw_type)
    dq_image_np = _arraytonumpy(shared_dq_image, shared_dq_image_shape, dtype=mp_dq_type)
    gain_np = _arraytonumpy(shared_gain, shared_gain_shape, dtype=mp_float_type)
    rdnoise_np = _arraytonumpy(shared_read_noise, shared_read_noise_shape, dtype=mp_float_type)

    results = []
    for row in range(block_start, block_end):
        args_row = (
            row,
            rejection_threshold,
            ramps_np[np.newaxis, :, [row], :],
            # Make sure to add a new axis to each array to maintain number of dimensions
            rdnoise_np[[row], :],
            gain_np[[row], :],
            dq_raw_np[np.newaxis, :, [row], :],
            dq_image_np[[row], :]
        )

        results.append(_jump_detection_jwst_row(args_row))

    for row_element in results:
        _row, _dq = row_element

        dq_raw_np[:, [_row], :] = _dq

    return (block_start, block_end)

def fit_ramps_jwst(
    times : np.ndarray,
    ramps : np.ndarray,
    dq_raw : np.ndarray = None,
    dq : np.ndarray = None,
    rdnoise : np.ndarray = None,
    gain : np.ndarray = None,
    dark_current : np.ndarray | None = None,
    start_times : np.ndarray | None = None,
    jump_detection : bool = False,
    jump_rejection_threshold : float = 4.0,
    max_cores : int = 1,
    algorithm : str = 'JWST_LIKELY',
) -> dict:
    """
    Fit ramps using JWST ramp fitting algorithms from stcal.ramp_fitting.

    Parameters
    ----------
    times : np.ndarray
        Read times.
    ramps : np.ndarray
        3D array of ramp data with shape (Nreads, Ny, Nx).
    dq_raw : np.ndarray, optional
        3D array of data quality flags across detector (Nreads, Ny, Nx)
    dq : np.ndarray, optional
        2D array of data quality flags across detector (Ny, Nx)
    rdnoise : np.ndarray, optional
        2D array of read noise across detector (Ny, Nx)
    gain : np.ndarray, optional
        2D array of gain across detector (Ny, Nx)
    dark_current : np.ndarray, optional
        2D array of dark current across detector (Ny, Nx)
    start_times : np.ndarray, optional
        MJD time of the start of the first read.
    jump_detection : bool, optional
        Whether to perform jump detection before ramp fitting. Default is False.
    jump_rejection_threshold : float, optional
        Sigma threshold for jump detection. Default is 4.0.
    max_cores : int, optional
        Number of cores for parallelization. Default is 1 (no parallelization).
    algorithm : str, optional
        Ramp fitting algorithm to use.  Options are 'JWST_LIKELY' or 'JWST_FOXSEN'. Default is 'JWST_LIKELY'.
    
    Returns
    -------
    output : dict[str, np.ndarray]
        Dictionary containing the L0 rate arrays.
    """

    n_reads, ny, nx = ramps.shape

    if algorithm.lower() in ('jwst_likely', 'jwst_like', 'jwst_likelihood'):
        algorithm = 'LIKELY'
    elif algorithm.lower() in ('jwst_fixsen', 'jwst_fixsen_c'):
        algorithm = 'FIXSEN_C'
    elif algorithm.lower() in ('cython_likely', 'cython_like', 'cython_likelihood'):
        algorithm = 'CYTHON_LIKELY'
    else:
        raise ValueError(f'Unrecognized JWST ramp fitting algorithm {algorithm}')

    if ramps.dtype is np.uint16:
        mp_data_type = ctypes.c_ushort
    else:
        mp_data_type = ctypes.c_float
    mp_float_type = ctypes.c_float
    mp_dq_raw_type = ctypes.c_uint8
    mp_dq_type = ctypes.c_uint
    types_tuple = (mp_data_type, mp_float_type, mp_dq_raw_type, mp_dq_type)

    slope_image_mp = RawArray(mp_float_type, nx * ny)
    slope_image_shape = (ny, nx)
    slope_image_np = _arraytonumpy(slope_image_mp, slope_image_shape, dtype=mp_float_type)
    slope_image_np[:] = np.zeros((ny, nx), dtype=np.float32)

    slope_errors_mp = RawArray(mp_float_type, nx * ny)
    slope_errors_shape = (ny, nx)
    slope_errors_np = _arraytonumpy(slope_errors_mp, slope_errors_shape, dtype=mp_float_type)
    slope_errors_np[:] = np.zeros((ny, nx), dtype=np.float32)

    var_poisson_image_mp = RawArray(mp_float_type, nx * ny)
    var_poisson_image_shape = (ny, nx)
    var_poisson_image_np = _arraytonumpy(var_poisson_image_mp, var_poisson_image_shape, dtype=mp_float_type)
    var_poisson_image_np[:] = np.zeros((ny, nx), dtype=np.float32)

    var_rnoise_image_mp = RawArray(mp_float_type, nx * ny)
    var_rnoise_image_shape = (ny, nx)
    var_rnoise_image_np = _arraytonumpy(var_rnoise_image_mp, var_rnoise_image_shape, dtype=mp_float_type)
    var_rnoise_image_np[:] = np.zeros((ny, nx), dtype=np.float32)

    dq_image_mp = RawArray(mp_dq_type, nx * ny)
    dq_image_shape = (ny, nx)
    dq_image_np = _arraytonumpy(dq_image_mp, dq_image_shape, dtype=mp_dq_type)
    if dq is None:
        dq_image_np[:] = np.zeros((ny, nx), dtype=np.uint32)
    else:
        dq_image_np[:] = dq

    start_times_mp = RawArray(mp_float_type, nx * ny)
    start_times_shape = (ny, nx)
    start_times_np = _arraytonumpy(start_times_mp, start_times_shape, dtype=mp_float_type)
    if start_times is None:
        start_times_np[:] = np.zeros((ny, nx), dtype=np.float32)
    else:
        start_times_np[:] = start_times

    mid_times_mp = RawArray(mp_float_type, nx * ny)
    mid_times_shape = (ny, nx)
    mid_times_np = _arraytonumpy(mid_times_mp, mid_times_shape, dtype=mp_float_type)
    mid_times_np[:] = np.zeros((ny, nx), dtype=np.float32)

    gain_mp = RawArray(mp_float_type, nx * ny)
    gain_shape = (ny, nx)
    gain_np = _arraytonumpy(gain_mp, gain_shape, dtype=mp_float_type)
    if gain is None:
        # TODO? - optimize gain when array is not passed
        gain_np[:] = np.ones((ny, nx), dtype=np.float32)
    else:
        gain_np[:] = gain

    dark_mp = RawArray(mp_float_type, nx * ny)
    dark_shape = (ny, nx)
    dark_np = _arraytonumpy(dark_mp, dark_shape, dtype=mp_float_type)
    if dark_current is None:
        dark_np[:] = np.zeros((ny, nx), dtype=np.float32)
    else:
        dark_np[:] = dark_current

    rdnoise_mp = RawArray(mp_float_type, nx * ny)
    rdnoise_shape = (ny, nx)
    rdnoise_np = _arraytonumpy(rdnoise_mp, dark_shape, dtype=mp_float_type)
    if rdnoise is None:
        # TODO? - optimize rdnoise when array is not passed
        rdnoise_np[:] = np.ones((ny, nx), dtype=np.float32)
    else:
        rdnoise_np[:] = rdnoise


    if max_cores > 1:

        ramps_mp = RawArray(mp_data_type, nx * ny * n_reads)
        ramps_shape = (n_reads, ny, nx)
        ramps_np = _arraytonumpy(ramps_mp, ramps_shape, dtype=mp_data_type)
        ramps_np[:] = ramps  # copy original array into shared array
        ramps = ramps_np  # free the original array from memory to avoid duplicates

        dq_raw_mp = RawArray(mp_dq_raw_type, nx * ny * n_reads)
        dq_raw_shape = (n_reads, ny, nx)
        dq_raw_np = _arraytonumpy(dq_raw_mp, dq_raw_shape, dtype=mp_dq_raw_type)
        if dq_raw is None:
            dq_raw_np[:] = np.zeros((n_reads, ny, nx), dtype=np.uint8)
        else:
            dq_raw_np[:] = dq_raw  # copy original array into shared array
            dq_raw = dq_raw_np  # free the original array from memory to avoid duplicates


        # Prepare blocks
        block_size = max(1, ny // (4*max_cores)) if max_cores > 1 else ny

        _init_args = (
            ramps_mp, ramps_shape,
            dq_raw_mp, dq_raw_shape,
            gain_mp, gain_shape,
            dark_mp, dark_shape,
            rdnoise_mp, rdnoise_shape,
            slope_image_mp, slope_image_shape,
            slope_errors_mp, slope_errors_shape,
            var_poisson_image_mp, var_poisson_image_shape,
            var_rnoise_image_mp, var_rnoise_image_shape,
            dq_image_mp, dq_image_shape,
            start_times_mp, start_times_shape,
            mid_times_mp, mid_times_shape
        )

        ctx = mp.get_context("spawn")  # avoids unsafe fork after OpenMP init
        tpool = ctx.Pool(
            processes=max_cores,
            initializer=_tpool_init_jwst_ramp,
            initargs=_init_args,
            maxtasksperchild=50
        )

        if jump_detection:
            args_list = []
            for block_start in range(0, ny, block_size):
                block_end = min(block_start + block_size, ny)

                args = (block_start, block_end, times, jump_rejection_threshold, types_tuple)
                args_list.append(args)

            tasks = [
                tpool.apply_async(_jump_detection_worker, args=(args_tuple,))
                for args_tuple in args_list
            ]

            for t in tqdm(tasks, desc="Processing blocks"):
                t.wait()

        args_list = []
        for block_start in range(0, ny, block_size):
            block_end = min(block_start + block_size, ny)

            args = (block_start, block_end, times, algorithm, types_tuple)
            args_list.append(args)

        try:
            with numba_thread_scope(max_cores):
                tasks = [
                    tpool.apply_async(_fit_ramps_worker, args=(args_tuple,))
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
        for row in np.arange(ny):
            #print(f"JWST Ramp Fitting: Processing row {row + 1} of {ny}.")

            if jump_detection:
                args_row = (
                    row,
                    jump_rejection_threshold,
                    ramps[np.newaxis, :, [row], :],
                    # Make sure to add a new axis to each array to maintain number of dimensions
                    rdnoise_np[[row], :],
                    gain_np[[row], :],
                    dq_raw[np.newaxis, :, [row], :],
                    dq_image_np[[row], :]
                )

                _row, _dq  = _jump_detection_jwst_row(args_row)
                dq_raw[:, [_row], :] = _dq

            args = (
                row,
                times,
                # Reshape to add the nints axis that JWST pipeline requires
                ramps[np.newaxis, :, [row], :],
                # Make sure to add a new axis to each array to maintain number of dimensions
                rdnoise_np[[row], :],
                gain_np[[row], :],
                dq_raw[np.newaxis, :, [row], :],
                dq_image_np[[row], :],
                dark_np[[row], :],
                algorithm
            )

            if algorithm == 'CYTHON_LIKELY':
                results.append(_fit_ramps_cython_row(args))
            else:
                results.append(_fit_ramps_jwst_row(args))

        for row_element in results:
            #row, outdata, dq, var_poisson, var_rnoise, err, chisq = row_element

            try:
                row = row_element['i']
            except:
                breakpoint()
            slope_image_np[row, :] = row_element['slope']
            slope_errors_np[row, :] = row_element['err']
            dq_image_np[row, :] = dq_image_np[row, :] | row_element['dq'][0]
            var_poisson_image_np[row, :] = row_element['var_poisson']
            var_rnoise_image_np[row, :] = row_element['var_rnoise']

        with numba_thread_scope(max_cores):
            mid_times_np = start_times + get_mid_delta_times(times, dq_raw)

    output = {}
    output['rate'] = slope_image_np
    output['rate_err'] = slope_errors_np
    output['rate_var_rnoise'] = var_rnoise_image_np
    output['rate_var_poisson'] = var_poisson_image_np
    output['mid_time'] = mid_times_np
    output['dq'] = dq_image_np

    return output

def _tpool_init_jwst_ramp(
    data : np.ndarray, data_shape : tuple,
    dq_raw : np.ndarray, dq_raw_shape : tuple,
    gain : np.ndarray, gain_shape : tuple,
    dark : np.ndarray, dark_shape : tuple,
    read_noise : np.ndarray, read_noise_shape : tuple,
    slope_image : np.ndarray, slope_image_shape : tuple,
    slope_errors : np.ndarray, slope_errors_shape : tuple,
    var_poisson_image : np.ndarray, var_poisson_image_shape : tuple,
    var_rnoise_image : np.ndarray, var_rnoise_image_shape : tuple,
    dq_image : np.ndarray, dq_image_shape : tuple,
    start_times : np.ndarray, start_times_shape : tuple,
    mid_times : np.ndarray, mid_times_shape : tuple
):
    """
    Initialize shared global variables for the multiprocessing pool.
    """

    global shared_data, shared_data_shape, \
        shared_dq_raw, shared_dq_raw_shape, \
        shared_gain, shared_gain_shape, \
        shared_dark, shared_dark_shape, \
        shared_read_noise, shared_read_noise_shape, \
        shared_slope_image, shared_slope_image_shape, \
        shared_slope_errors, shared_slope_errors_shape, \
        shared_var_poisson_image, shared_var_poisson_image_shape, \
        shared_var_rnoise_image, shared_var_rnoise_image_shape, \
        shared_dq_image, shared_dq_image_shape, \
        shared_start_times, shared_start_times_shape, \
        shared_mid_times, shared_mid_times_shape

    shared_data = data
    shared_data_shape = data_shape

    shared_dq_raw = dq_raw
    shared_dq_raw_shape = dq_raw_shape

    shared_gain = gain
    shared_gain_shape = gain_shape

    shared_dark = dark
    shared_dark_shape = dark_shape

    shared_read_noise = read_noise
    shared_read_noise_shape = read_noise_shape

    shared_slope_image = slope_image
    shared_slope_image_shape = slope_image_shape

    shared_slope_errors = slope_errors
    shared_slope_errors_shape = slope_errors_shape

    shared_var_poisson_image = var_poisson_image
    shared_var_poisson_image_shape = var_poisson_image_shape

    shared_var_rnoise_image = var_rnoise_image
    shared_var_rnoise_image_shape = var_rnoise_image_shape

    shared_dq_image = dq_image
    shared_dq_image_shape = dq_image_shape

    shared_start_times = start_times
    shared_start_times_shape = start_times_shape

    shared_mid_times = mid_times
    shared_mid_times_shape = mid_times_shape