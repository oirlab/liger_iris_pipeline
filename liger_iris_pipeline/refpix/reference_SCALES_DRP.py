# From SCALES DRP: Reference Pixel Correction
# Author: Athira Unni
# Primitive copied from https://github.com/scalessim/SCALES-DRP/blob/main/scalesdrp/primitives/reference.py on 2026-01-03

# import pandas as pd
import numpy as np
from astropy.io import fits
# import warnings
# warnings.filterwarnings("ignore", category=RuntimeWarning)
# import pkg_resources
import os
from scipy.optimize import minimize
import astropy.io.fits as pyfits
import scipy.sparse as sp
import matplotlib.pyplot as plt
import time
#####
# 2026-01-03 JB Ruffio: Hack to use normal numpy statistics as opposed to the robust module from the SCALES DRP
# import scalesdrp.primitives.robust as robust
import numpy as robust
#####
from scipy.optimize import leastsq
# import pkg_resources
from scipy.signal import savgol_filter



def reffix_hxrg(cube, nchans=4, in_place=False, fixcol=True, **kwargs):
    # Make sure we work in float32
    arr = np.asarray(cube)
    if not np.issubdtype(arr.dtype, np.floating):
        # must copy when changing dtype
        arr = arr.astype(np.float32, copy=True)
    elif not in_place:
        arr = arr.copy()

    # 1) Channel bias (use altcol=False if you're doing ACN next)
    arr = reffix_amps(arr, nchans=nchans, in_place=True, **kwargs)

    # 2) ACN (even/odd row-dependent using side refs)
    arr = acn_filter(arr, in_place=True, **kwargs)

    # 3) 1/f row stripes (side refs, common-mode)
    if fixcol:
        arr = ref_filter(arr, nchans=nchans, in_place=True, **kwargs)

    return arr

############ ACN & CHANNEL BIAS OLD #########################
def reffix_amps_old(cube, nchans=4, in_place=True, altcol=True, supermean=False,
    top_ref=True, bot_ref=True, ntop=4, nbot=4, **kwargs):

    """
    Correct amplifier offsets
    Matches all amplifier outputs of the detector to a common level.
    This routine subtracts the average of the top and bottom reference rows
    for each amplifier and frame individually.
    
    Parameters
    ----------
    cube : ndarray
        Input datacube. Can be two or three dimensions (nz,ny,nx).
    nchans : int
        Number of output amplifier channels in the detector. Default=4.
    altcol : bool
        Calculate separate reference values for even/odd columns.
    supermean : bool
        Add back the overall mean of the reference pixels.
    in_place : bool
        Perform calculations in place. Input array is overwritten.
    top_ref : bool
        Include top reference rows when correcting channel offsets.
    bot_ref : bool
        Include bottom reference rows when correcting channel offsets.
    ntop : int
        Specify the number of top reference rows.
    nbot : int
        Specify the number of bottom reference rows.
    mean_func : func
        Function used to calculate averages.
    """
    if not np.issubdtype(cube.dtype, np.floating):
        cube = cube.astype(np.float32, copy=not in_place)
        in_place = True

    if not in_place:
        cube = np.copy(cube)
    ndim = len(cube.shape)
    if ndim==2:
        ny,nx = cube.shape
        nz = 1
        cube = cube.reshape((nz,ny,nx))
    elif ndim==3:
        nz, ny, nx = cube.shape
    else:
        raise ValueError('Input data can only have 2 or 3 dimensions.Found {} dimensions.'.format(ndim))

    chsize = int(nx / nchans)
    # Number of reference rows to use
    # Set nt or nb equal to 0 if we don't want to use either
    nt = ntop if top_ref else 0
    nb = nbot if bot_ref else 0
    if (nt+nb)==0:
        print("No reference pixels available for use. Returning...")
        return
    # Slice out reference pixels
    refs_bot = cube[:,:nb,:]
    refs_top = cube[:,-nt:,:]
    if nt==0:
        refs_all = refs_bot
    elif nb==0:
        refs_all = refs_top
    else:
        refs_all = np.hstack((refs_bot, refs_top))
    assert refs_all.shape[1] == (nb+nt)

    # Supermean
    # the average of the average is the DC level of the output channel
    smean = robust.mean(refs_all) if supermean else 0.0
    # Calculate avg reference values for each frame and channel
    #refs_all(reads,8,2048)
    refs_amps_avg = calc_avg_amps_old(refs_all, cube.shape, nchans=nchans, altcol=altcol, **kwargs)
    #(4,2, 1, 1) ==> altcol=False (channel, reads,1,1)
    #(2,2,4) ==> altcol=True [odd/even][channel,reads)
    for ch in range(nchans):
        # Channel indices
        ich1 = ch*chsize
        ich2 = ich1 + chsize
        #print(ich1)
        # In-place subtraction of channel medians
        if altcol:
            for i in range(nz):
                cube[i,:,ich1:ich2-1:2] -= refs_amps_avg[0][ch,i]
                cube[i,:,ich1+1:ich2:2] -= refs_amps_avg[1][ch,i]
        else:
            for i in range(nz):
                cube[i,:,ich1:ich2] -= refs_amps_avg[ch,i]
    # Add back supermean
    if supermean:
        cube += smean
    cube = cube.squeeze()
    return cube

def calc_avg_amps_old(refs_all, data_shape, nchans=4, altcol=True, mean_func=robust.mean, **kwargs):
    #refs_all(reads,8,2048)
    nz, ny, nx = data_shape
    chsize = int(nx / nchans)
    if altcol:
        refs_amps_avg1 = []
        refs_amps_avg2 = []
        for ch in range(nchans):
            ich1 = ch*chsize
            ich2 = ich1 + chsize
            #extracts every other column in the range [ich1, ich2) &  flattens everything except nz
            refs_ch1 = refs_all[:,:,ich1:ich2-1:2].reshape((nz,-1)) #even
            refs_ch2 = refs_all[:,:,ich1+1:ich2:2].reshape((nz,-1)) #odd
            chavg1 = mean_func(refs_ch1,axis=1) ##one scalar per amp per frame.
            chavg2 = mean_func(refs_ch2,axis=1)
            refs_amps_avg1.append(chavg1)
            refs_amps_avg2.append(chavg2)
        # return one odd and one even value for each channel and each read
        return (np.array(refs_amps_avg1), np.array(refs_amps_avg2))
    else:
        refs_amps_avg = []
        for ch in range(nchans):
            ich1 = ch*chsize
            ich2 = ich1 + chsize
            refs_ch = refs_all[:,:,ich1:ich2].reshape((nz,-1))
            chavg = mean_func(refs_ch,axis=1).reshape([-1,1,1])
            refs_amps_avg.append(chavg)
        #return one value for each channel and each read
        return np.array(refs_amps_avg)

################################## NEW acn ################################
def reffix_amps(cube, nchans=4, in_place=True, altcol=False, supermean=False,
    top_ref=True, bot_ref=True, ntop=4, nbot=4, **kwargs):

    """Correct amplifier offsets
    Matches all amplifier outputs of the detector to a common level.
    This routine subtracts the average of the top and bottom reference rows
    for each amplifier and frame individually.
    
    Parameters
    ----------
    cube : ndarray
        Input datacube. Can be two or three dimensions (nz,ny,nx).
    nchans : int
        Number of output amplifier channels in the detector. Default=4.
    altcol : bool
        Calculate separate reference values for even/odd columns.
    supermean : bool
        Add back the overall mean of the reference pixels.
    in_place : bool
        Perform calculations in place. Input array is overwritten.
    top_ref : bool
        Include top reference rows when correcting channel offsets.
    bot_ref : bool
        Include bottom reference rows when correcting channel offsets.
    ntop : int
        Specify the number of top reference rows.
    nbot : int
        Specify the number of bottom reference rows.
    mean_func : func
        Function used to calculate averages.
    """
    if not np.issubdtype(cube.dtype, np.floating):
        cube = cube.astype(np.float32, copy=not in_place)
        in_place = True

    if not in_place:
        cube = np.copy(cube)
    ndim = len(cube.shape)
    if ndim==2:
        ny,nx = cube.shape
        nz = 1
        cube = cube.reshape((nz,ny,nx))
    elif ndim==3:
        nz, ny, nx = cube.shape
    else:
        raise ValueError('Input data can only have 2 or 3 dimensions.Found {} dimensions.'.format(ndim))

    chsize = int(nx / nchans)
    # Number of reference rows to use
    # Set nt or nb equal to 0 if we don't want to use either
    nt = ntop if top_ref else 0
    nb = nbot if bot_ref else 0
    if (nt+nb)==0:
        print("No reference pixels available for use. Returning...")
        return
    # Slice out reference pixels
    refs_bot = cube[:,:nb,:]
    refs_top = cube[:,-nt:,:]
    if nt==0:
        refs_all = refs_bot
    elif nb==0:
        refs_all = refs_top
    else:
        refs_all = np.hstack((refs_bot, refs_top))
    assert refs_all.shape[1] == (nb+nt)

    # Supermean
    # the average of the average is the DC level of the output channel
    smean = robust.mean(refs_all) if supermean else 0.0
    # Calculate avg reference values for each frame and channel
    #refs_all(reads,8,2048)
    refs_amps_avg = calc_avg_amps(refs_all, cube.shape, nchans=nchans, altcol=altcol, **kwargs)
    #print(refs_amps_avg)
    for ch in range(nchans):
        # Channel indices
        ich1 = ch*chsize
        ich2 = ich1 + chsize
        #print(ich1)
        # In-place subtraction of channel medians
        if altcol:
            for i in range(nz):
                cube[i,:,ich1:ich2-1:2] -= refs_amps_avg[0][ch,i]
                cube[i,:,ich1+1:ich2:2] -= refs_amps_avg[1][ch,i]
        else:
            for i in range(nz):
                offs = refs_amps_avg[ch, i][np.newaxis, :]   # (1, chsize)
                cube[i, :, ich1:ich2] -= offs
    # Add back supermean
    if supermean:
        cube += smean
    cube = cube.squeeze()
    return cube


def calc_avg_amps(refs_all, data_shape, nchans=4, altcol=False,
                  mean_func=robust.mean, **kwargs):
    """
    Compute average reference values per amplifier.

    Parameters
    ----------
    refs_all : ndarray
        Reference pixels for bottom + top rows, shape (nz, nref, nx).
    data_shape : tuple
        Full data shape (nz, ny, nx) of the science cube.
    nchans : int
        Number of amplifier channels along the x-axis.
    altcol : bool
        If True, compute separate averages for even/odd columns (JWST-style).
        If False, compute a separate value for *each column* in each amp.
    mean_func : callable
        Function used to calculate averages (e.g., robust.mean, np.nanmedian).
    """
    # Use refs_all to infer nz, nx (nref doesn't matter)
    nz_ref, nref, nx = refs_all.shape
    nz, ny, nx_full = data_shape
    assert nx == nx_full, "refs_all and data_shape nx mismatch"
    assert nz_ref == nz,  "refs_all and data_shape nz mismatch"

    chsize = nx // nchans

    if altcol:
        # one even and one odd value per amp+frame
        refs_amps_avg1 = []
        refs_amps_avg2 = []
        for ch in range(nchans):
            ich1 = ch * chsize
            ich2 = ich1 + chsize

            # Even and odd columns within this channel
            refs_ch1 = refs_all[:, :, ich1:ich2-1:2].reshape((nz, -1))  # even
            refs_ch2 = refs_all[:, :, ich1+1:ich2:2].reshape((nz, -1))  # odd

            chavg1 = mean_func(refs_ch1, axis=1)  # (nz,)
            chavg2 = mean_func(refs_ch2, axis=1)  # (nz,)

            refs_amps_avg1.append(chavg1)
            refs_amps_avg2.append(chavg2)

        # Shape: (2, nchans, nz)
        return (np.array(refs_amps_avg1), np.array(refs_amps_avg2))

    else:
        # --- column-wise averages per amp+frame ---
        # We want: refs_amps_avg[ch, i, k] = mean over ref rows for that column
        refs_amps_avg = np.empty((nchans, nz, chsize), dtype=np.float32)

        for ch in range(nchans):
            ich1 = ch * chsize
            ich2 = ich1 + chsize

            # Extract refs for this amp: (nz, nref, chsize)
            refs_ch = refs_all[:, :, ich1:ich2]

            # Average over reference rows axis=1 → (nz, chsize)
            # i.e., per frame, per column
            chavg = mean_func(refs_ch, axis=1)  # (nz, chsize)

            refs_amps_avg[ch] = chavg.astype(np.float32)

        # Shape: (nchans, nz, chsize)
        return refs_amps_avg

############# additional acn ###################################

def acn_filter(cube,
               in_place=True,
               avg_type='pix',
               perint=False,
               edge_wrap=False,
               left_ref=True,
               right_ref=True,
               nleft=4,
               nright=4,
               mean_func=np.median,
               **kwargs):
    """
    Row-dependent differences between even and odd columns
    (i.e. ACN that changes with row, not just a constant offset per column).
    They are row-series describing how the even or odd reference pixels
    vary vs row (and frame), after baseline removal.

    ACN correction using side reference columns.
    Separately estimates row-dependent even and odd column offsets,
    then subtracts them from the full image.

    Parameters
    ----------
    cube : ndarray
        Input data:
          - (H, W)  single frame, or
          - (N, H, W) stack of frames.
    in_place : bool
        If False, the input array will be copied.
    avg_type : {'pix', 'frame', 'int'}
        Baseline removal mode for reference pixels:
            - 'pix'   : remove per-pixel mean over integration (best for many frames).
            - 'frame' : remove per-frame global mean of refs.
            - 'int'   : remove a single global mean over the whole ramp.
    perint : bool
        Passed to `calc_col_smooth`: smooth per integration instead of per frame.
    edge_wrap : bool
        Passed to `calc_col_smooth`: mirror edges before smoothing to reduce ringing.
    left_ref, right_ref : bool
        Whether to use left and/or right side reference columns.
    nleft, nright : int
        Number of left/right reference columns to use.
    mean_func : callable
        Function to compute averages (e.g., np.median or robust.mean).

    Returns
    -------
    out : ndarray
        ACN-corrected array (same shape as input, float32).
    """
    arr = np.asarray(cube)
    print(arr.shape)
    if arr.ndim == 2:
        single_frame = True
        arr = arr[np.newaxis, ...]   # (1, H, W)
    elif arr.ndim == 3:
        single_frame = False
    else:
        raise ValueError(f"acn_filter: input must be 2D or 3D, got shape {arr.shape}")

    if not in_place:
        arr = np.copy(arr)

    N, H, W = arr.shape

    # Decide how many side references we actually use
    nl = nleft  if left_ref  else 0
    nr = nright if right_ref else 0

    if nl < 0 or nr < 0:
        raise ValueError("nleft and nright must be non-negative.")
    if (nl + nr) == 0:
        print("acn_filter: No side reference columns enabled. Returning input.")
        return cube

    out = arr.astype(np.float32, copy=True)

    # Slice side reference columns
    refs_left  = out[:, :, :nl]   if nl > 0 else None  # (N, H, nl)
    refs_right = out[:, :, -nr:]  if nr > 0 else None  # (N, H, nr)

    def _normalize_and_avg(refs_left, refs_right, avg_type, mean_func):
        """
        Given left/right refs for even or odd,
        perform avg_type baseline removal and then average along columns
        to get (N, H) row-wise reference values.
        """
        nl_flag = 0 if refs_left  is None else 1
        nr_flag = 0 if refs_right is None else 1

        if nl_flag == 0 and nr_flag == 0:
            # No refs for this parity at all; return zeros
            return np.zeros((N, H), dtype=np.float32)

        # Make copies so we don't mutate outer refs
        if nl_flag:
            refs_left = np.copy(refs_left)
            Nloc, Hloc, Cleft = refs_left.shape
        if nr_flag:
            refs_right = np.copy(refs_right)
            if not nl_flag:
                Nloc, Hloc, Cright = refs_right.shape
            else:
                _, _, Cright = refs_right.shape

        if avg_type is None:
            mode = 'frame'
        else:
            mode = avg_type

        if Nloc == 1:
            mode = 'int'  # 'int' == 'frame' when only one frame

        # ---- Remove intrinsic offsets depending on mode ----
        if 'int' in mode:
            # One global scalar over the integration
            #compute single scalar value over frames and all left and right reference
            if nl_flag:
                refs_left  -= mean_func(refs_left)
            if nr_flag:
                refs_right -= mean_func(refs_right)

        elif 'frame' in mode:
            # One scalar per frame
            if nl_flag:
                rl_flat = refs_left.reshape(Nloc, -1)
                rl_mean = mean_func(rl_flat, axis=1)
                plt.figure()
                plt.title('left')
                plt.plot(rl_mean)
                plt.show()
                for i in range(Nloc):
                    refs_left[i] -= rl_mean[i]
            if nr_flag:
                rr_flat = refs_right.reshape(Nloc, -1)
                rr_mean = mean_func(rr_flat, axis=1)
                plt.figure()
                plt.title('right')
                plt.plot(rr_mean)
                plt.show()
                for i in range(Nloc):
                    refs_right[i] -= rr_mean[i]

        elif 'pix' in mode:
            # Per-pixel mean over frames
            if nl_flag:
                rl_mean = mean_func(refs_left, axis=0)   # (H, Cleft)
                #print(rl_mean.shape)
                #print(np.where(np.isnan(rl_mean)==True))
                #plt.figure()
                #plt.plot(rl_mean)
                #plt.show()
                for i in range(Nloc):
                    refs_left[i] -= rl_mean
                    #plt.figure()
                    #plt.title('acn using left side ref')
                    #plt.plot(refs_left[i])
                #plt.show()
            if nr_flag:
                rr_mean = mean_func(refs_right, axis=0)  # (H, Cright)
                #print(np.where(np.isnan(rr_mean)==True))
                #plt.figure()
                #plt.plot(rr_mean)
                #plt.show()
                for i in range(Nloc):
                    refs_right[i] -= rr_mean
                    #plt.figure()
                    #plt.title('acn using right side ref')
                    #plt.plot(refs_left[i])
                #plt.show()

        # ---- Average left/right columns down to a single value per row ----
        if nl_flag == 0:
            refs_side_avg = refs_right.mean(axis=2)      # (N, H)
        elif nr_flag == 0:
            refs_side_avg = refs_left.mean(axis=2)       # (N, H)
        else:
            # Average left and right
            refs_side_avg = (refs_left.mean(axis=2) + refs_right.mean(axis=2)) / 2.0

        return refs_side_avg.astype(np.float32)

    # --- Split side refs into even/odd columns

    # Global column indices
    cols = np.arange(W) #W is 4

    # Left side global indices: 0 .. nl-1
    if nl > 0:
        left_cols = cols[:nl]
        left_even_mask = (left_cols % 2) == 0
        left_odd_mask  = ~left_even_mask
        refs_left_even = refs_left[:, :, left_even_mask] if left_even_mask.any() else None
        refs_left_odd  = refs_left[:, :, left_odd_mask]  if left_odd_mask.any()  else None
    else:
        refs_left_even = refs_left_odd = None

    # Right side global indices: W-nr .. W-1
    if nr > 0:
        right_cols = cols[-nr:]
        right_even_mask = (right_cols % 2) == 0
        right_odd_mask  = ~right_even_mask
        refs_right_even = refs_right[:, :, right_even_mask] if right_even_mask.any() else None
        refs_right_odd  = refs_right[:, :, right_odd_mask]  if right_odd_mask.any()  else None
    else:
        refs_right_even = refs_right_odd = None

    # --- Compute raw row-wise ACN refs for even and odd separately ---

    # Shape (N, H) each
    ref_even = _normalize_and_avg(refs_left_even, refs_right_even, avg_type, mean_func) #(2,2048)
    ref_odd  = _normalize_and_avg(refs_left_odd,  refs_right_odd,  avg_type, mean_func) #(2,2048)

    # --- Smooth them (FFT or SavGol), same as ref_filter / calc_col_smooth ---

    ref_even_sm = calc_col_smooth(ref_even, out.shape,
                                  perint=perint,
                                  edge_wrap=edge_wrap,
                                  delt=kwargs.get('delt', 5.24e-4),
                                  savgol=kwargs.get('savgol', False),
                                  winsize=kwargs.get('winsize', 31),
                                  order=kwargs.get('order', 3))
    ref_odd_sm  = calc_col_smooth(ref_odd,  out.shape,
                                  perint=perint,
                                  edge_wrap=edge_wrap,
                                  delt=kwargs.get('delt', 5.24e-4),
                                  savgol=kwargs.get('savgol', False),
                                  winsize=kwargs.get('winsize', 31),
                                  order=kwargs.get('order', 3))

    # --- Subtract from even/odd columns across the entire image ---
    #Each row y gets: one subtraction for even columns (ref_even_sm[:, y]),
    #one subtraction for odd columns (ref_odd_sm[:, y]).

    even_cols = cols[cols % 2 == 0]
    odd_cols  = cols[cols % 2 == 1]

    if even_cols.size > 0:
        out[:, :, even_cols] -= ref_even_sm.reshape(N, H, 1)
    if odd_cols.size > 0:
        out[:, :, odd_cols]  -= ref_odd_sm.reshape(N, H, 1)

    if single_frame:
        return out[0]
    return out

import numpy as np

def acn_filter_nobaserm(
    cube,
    in_place=True,
    perint=False,
    edge_wrap=False,
    left_ref=True,
    right_ref=True,
    nleft=4,
    nright=4,
    mean_func=np.median,   # still used for averaging over columns
    **kwargs
):
    """
    ACN correction using side reference columns, *without* any baseline/mean removal.

    This version uses the raw left/right reference pixel values (after top/bottom
    correction), averaged over reference columns, then smoothed vs. row, and
    subtracted from even/odd columns.

    Parameters
    ----------
    cube : ndarray
        Input data:
            - (H, W)  single frame, or
            - (N, H, W) stack of frames.

    in_place : bool
        If False, the input array will be copied.
    perint : bool
        Passed to `calc_col_smooth`: smooth per integration instead of per frame.
    edge_wrap : bool
        Passed to `calc_col_smooth`: mirror edges before smoothing to reduce ringing.
    left_ref, right_ref : bool
        Whether to use left and/or right side reference columns.
    nleft, nright : int
        Number of left/right reference columns to use.
    mean_func : callable
        Function to combine multiple reference columns (e.g., np.median).
        NOTE: this function is *not* used for baseline subtraction here,
        only for averaging across columns.

    Returns
    -------
    out : ndarray
        ACN-corrected array (same shape as input, float32).
    """
    arr = np.asarray(cube)

    # --- Normalize dimensionality to (N, H, W) ---
    if arr.ndim == 2:
        single_frame = True
        arr = arr[np.newaxis, ...]  # (1, H, W)
    elif arr.ndim == 3:
        single_frame = False
    else:
        raise ValueError(f"acn_filter_nobase: input must be 2D or 3D, got shape {arr.shape}")

    if not in_place:
        arr = np.copy(arr)

    N, H, W = arr.shape

    # --- Decide how many side refs we actually use ---
    nl = nleft  if left_ref  else 0
    nr = nright if right_ref else 0

    if nl < 0 or nr < 0:
        raise ValueError("nleft and nright must be non-negative.")
    if (nl + nr) == 0:
        print("acn_filter_nobase: No side reference columns enabled. Returning input.")
        return cube

    out = arr.astype(np.float32, copy=True)

    # --- Slice side reference columns from the full image ---
    refs_left  = out[:, :, :nl]   if nl > 0 else None  # (N, H, nl)
    refs_right = out[:, :, -nr:]  if nr > 0 else None  # (N, H, nr)

    def _avg_refs(refs_left, refs_right):
        """
        Given left/right refs for a particular parity (even or odd),
        simply average over reference columns to get (N, H) row-wise values.
        NO baseline / mean removal is done here.
        """
        nl_flag = 0 if refs_left  is None else 1
        nr_flag = 0 if refs_right is None else 1

        if nl_flag == 0 and nr_flag == 0:
            # No refs for this parity at all; return zeros
            return np.zeros((N, H), dtype=np.float32)

        # Average across ref columns (axis=2)
        if nl_flag == 0:
            refs_side_avg = mean_func(refs_right, axis=2)        # (N, H)
        elif nr_flag == 0:
            refs_side_avg = mean_func(refs_left,  axis=2)        # (N, H)
        else:
            left_avg  = mean_func(refs_left,  axis=2)            # (N, H)
            right_avg = mean_func(refs_right, axis=2)            # (N, H)
            refs_side_avg = 0.5 * (left_avg + right_avg)

        return refs_side_avg.astype(np.float32)

    # --- Split side refs into even/odd columns (global parity) ---

    cols = np.arange(W)

    # Left side global indices: 0 .. nl-1
    if nl > 0:
        left_cols = cols[:nl]
        left_even_mask = (left_cols % 2) == 0
        left_odd_mask  = ~left_even_mask
        refs_left_even = refs_left[:, :, left_even_mask] if left_even_mask.any() else None
        refs_left_odd  = refs_left[:, :, left_odd_mask]  if left_odd_mask.any()  else None
    else:
        refs_left_even = refs_left_odd = None

    # Right side global indices: W-nr .. W-1
    if nr > 0:
        right_cols = cols[-nr:]
        right_even_mask = (right_cols % 2) == 0
        right_odd_mask  = ~right_even_mask
        refs_right_even = refs_right[:, :, right_even_mask] if right_even_mask.any() else None
        refs_right_odd  = refs_right[:, :, right_odd_mask]  if right_odd_mask.any()  else None
    else:
        refs_right_even = refs_right_odd = None

    # --- Build row-wise ACN refs for even and odd, using RAW refs (no baseline removal) ---

    # Shapes: (N, H)
    ref_even = _avg_refs(refs_left_even, refs_right_even)
    ref_odd  = _avg_refs(refs_left_odd,  refs_right_odd)

    # --- Smooth them (FFT or SavGol), same as ref_filter / calc_col_smooth ---

    ref_even_sm = calc_col_smooth(
        ref_even,
        out.shape,
        perint=perint,
        edge_wrap=edge_wrap,
        delt=kwargs.get('delt', 5.24e-4),
        savgol=kwargs.get('savgol', False),
        winsize=kwargs.get('winsize', 31),
        order=kwargs.get('order', 3),
    )

    ref_odd_sm = calc_col_smooth(
        ref_odd,
        out.shape,
        perint=perint,
        edge_wrap=edge_wrap,
        delt=kwargs.get('delt', 5.24e-4),
        savgol=kwargs.get('savgol', False),
        winsize=kwargs.get('winsize', 31),
        order=kwargs.get('order', 3),
    )

    # --- Subtract from even/odd columns across the entire image ---

    even_cols = cols[cols % 2 == 0]
    odd_cols  = cols[cols % 2 == 1]

    if even_cols.size > 0:
        out[:, :, even_cols] -= ref_even_sm.reshape(N, H, 1)
    if odd_cols.size > 0:
        out[:, :, odd_cols]  -= ref_odd_sm.reshape(N, H, 1)

    if single_frame:
        return out[0]
    return out

############################# 1/f ################################################

def ref_filter(cube, nchans=4, in_place=True, avg_type='pix', perint=False,
    edge_wrap=False, left_ref=True, right_ref=True, nleft=4, nright=4, **kwargs):
    """
    Optimal Smoothing
    Performs an optimal filtering of the vertical reference pixel to
    reduce 1/f noise (horizontal stripes).
    FFT method adapted from M. Robberto IDL code:
    http://www.stsci.edu/~robberto/Main/Software/IDL4pipeline/

    Parameters
    ----------
    cube : ndarray
        Input datacube. Can be two or three dimensions (nz,ny,nx).
    nchans : int
        Number of output amplifier channels in the detector. Default=4.
    in_place : bool
        Perform calculations in place. Input array is overwritten.
    perint : bool
        Smooth side reference pixel per integration,
        otherwise do frame-by-frame.
    avg_type : str
        Type of ref col averaging to perform. Allowed values are
        'pix', 'frame', or 'int'.
    left_ref : bool
        Include left reference cols when correcting 1/f noise.
    right_ref : bool
        Include right reference cols when correcting 1/f noise.
    nleft : int
        Specify the number of left reference columns.
    nright : int
        Specify the number of right reference columns.
    savgol : bool
        Using Savitsky-Golay filter method rather than FFT.
    winsize : int
        Size of the window filter.
    order : int
        Order of the polynomial used to fit the samples.
    mean_func : func
        Function to use to calculate averages of reference columns.
    """
    if not in_place:
        cube = np.copy(cube)
    ndim = len(cube.shape)
    if ndim==2:
        ny,nx = cube.shape
        nz = 1
        cube = cube.reshape((nz,ny,nx))
    elif ndim==3:
        nz, ny, nx = cube.shape
    else:
        raise ValueError('Input data can only have 2 or 3 dimensions. Found {} dimensions.'.format(ndim))

    # Number of reference rows to use
    # Set nt or nb equal to 0 if we don't want to use either
    nl = nleft  if left_ref  else 0
    nr = nright if right_ref else 0
    assert nl>=0, 'Number of left reference pixels must not be negative.'
    assert nr>=0, 'Number of right reference pixels must not be negative.'
    if (nl+nr)==0:
        print("No reference pixels available for use. Returning...")
        return
    # Slice out reference pixel columns
    refs_left  = cube[:,:,:nl]  if nl>0 else None
    refs_right = cube[:,:,-nr:] if nr>0 else None
    refvals = calc_avg_cols(refs_left, refs_right, avg_type, **kwargs)
    #refvals = calc_avg_cols_no_baseline(refs_left, refs_right)
    # approximate x axis for smoothening
    delt = 10E-6 * (nx/nchans + 12.)
    refvals_smoothed = calc_col_smooth(refvals, cube.shape, perint=perint,
        edge_wrap=edge_wrap, delt=delt, **kwargs)
    # Final correction
    #for i,im in enumerate(cube): im -= refvals_smoothed[i].reshape([ny,1])
    cube -= refvals_smoothed.reshape([nz,ny,1])
    cube = cube.squeeze()
    return cube

def calc_avg_cols_no_baseline(refs_left=None, refs_right=None):
    """
    Same output as calc_avg_cols(), but does NOT remove
    reference pixel means / DC offsets.

    Useful for comparison — this version allows reference pixel
    fixed-pattern biases to leak directly into the correction vector.

    Parameters
    ----------
    refs_left : ndarray or None
        Left reference strip, shape (N, H, nleft)
    refs_right : ndarray or None
        Right reference strip, shape (N, H, nright)

    Returns
    -------
    refs_side_avg : ndarray  (N, H)
        Row-averaged reference drift without mean removal.
    """

    nl = 0 if refs_left  is None else 1
    nr = 0 if refs_right is None else 1

    if nl == 0 and nr == 0:
        return None  # nothing to return

    # Copy so we don't modify caller data
    if nl > 0:
        refs_left  = np.copy(refs_left)
    if nr > 0:
        refs_right = np.copy(refs_right)

    # ---- NO baseline normalization performed here ----
    # Simply collapse reference pixels to one value per row

    if nl == 0:
        refs_side_avg = refs_right.mean(axis=2)  # shape (N, H)
    elif nr == 0:
        refs_side_avg = refs_left.mean(axis=2)   # shape (N, H)
    else:
        refs_side_avg = (refs_left.mean(axis=2) +
                         refs_right.mean(axis=2)) / 2.0

    return refs_side_avg.astype(np.float32)



def calc_avg_cols(refs_left=None, refs_right=None, avg_type='pix',
    mean_func=np.median, **kwargs):
    """
    Calculate average of column references
    Determine the average values for the column references, which
    is subsequently used to estimate the 1/f noise contribution.
    
    Parameters
    ----------
    refs_left : ndarray
        Left reference columns.
    refs_right : ndarray
        Right reference columns.
    avg_type : str
        Type of ref column averaging to perform to determine ref pixel variation.
        Allowed values are 'pixel', 'frame', or 'int'.

            - 'pixel' : For each ref pixel, subtract its avg value from all frames.
            - 'frame' : For each frame, get avg ref pixel values and subtract framewise.
            - 'int'   : Calculate avg of all ref pixels within the ramp and subtract.

    mean_func : func
        Function to use to calculate averages of reference columns
    """
    # Which function to use for calculating averages?
    # mean_func = robust.mean
    # mean_func = np.median

    # In this context, nl and nr are either 0 (False) or 1 (True)
    nl = 0 if refs_left is None else 1
    nr = 0 if refs_right is None else 1

    # Left and right reference pixels
    # Make a copy so as to not modify the original data
    if nl>0: refs_left  = np.copy(refs_left)
    if nr>0: refs_right = np.copy(refs_right)

    # Set the average of left and right reference pixels to zero
    # By default, pixel averaging is best for large groups

    if avg_type is None:
        avg_type = 'frame'
    if refs_left is not None:
        nz, ny, nchan = refs_left.shape
    else:
        nz, ny, nchan = refs_right.shape
        # If there is only 1 frame, then we have to do "per frame" averaging.
        # Set to "per int", which produces the same result as "per frame" for nz=1.
    if nz==1:
        avg_type = 'int'
        # Remove average ref pixel values
        # Average over entire integration
    if 'int' in avg_type:
        if nl>0: refs_left  -= mean_func(refs_left) #refs_left now contains only deviations from that global mean.
        if nr>0: refs_right -= mean_func(refs_right)
    # Average over each frame
    #'frame' mode remove a frame-by-frame DC offset,
    #leaving row-dependent fluctuations within each frame.
    #
    elif 'frame' in avg_type:
        if nl>0: refs_left_mean  = mean_func(refs_left.reshape((nz,-1)), axis=1)#flatten each frame’s ref pixels to 1D, one scalar per frame.
        if nr>0: refs_right_mean = mean_func(refs_right.reshape((nz,-1)), axis=1)
        # Subtract estimate of each ref pixel "intrinsic" value
        for i in range(nz):
            if nl>0: refs_left[i]  -= refs_left_mean[i]
            if nr>0: refs_right[i] -= refs_right_mean[i]
    # Take the average of each reference pixel
    #gives an average for each reference pixel position over all frames
    #Subtracting this from each frame removes each pixel’s own intrinsic bias pattern.
    elif 'pix' in avg_type:
        if nl>0:
            refs_left_mean  = mean_func(refs_left, axis=0) #(2048, 4)
        if nr>0:
            refs_right_mean = mean_func(refs_right, axis=0)
        # Subtract estimate of each ref pixel "intrinsic" value
        for i in range(nz):
            if nl>0: refs_left[i]  -= refs_left_mean
            if nr>0: refs_right[i] -= refs_right_mean

    if nl==0: #ref_left is none
        refs_side_avg = refs_right.mean(axis=2)#averages over all left reference columns
    elif nr==0: #ref_right is none
        refs_side_avg = refs_left.mean(axis=2)
    else:
        refs_side_avg = (refs_right.mean(axis=2) + refs_left.mean(axis=2)) / 2
    return refs_side_avg #(2, 2048)

def calc_col_smooth(refvals, data_shape, perint=False, edge_wrap=False,
    delt=5.24E-4, savgol=False, winsize=31, order=3, **kwargs):
    """
    Perform optimal smoothing of side ref pix
    Generates smoothed version of column reference values.
    Smooths values from calc_avg_cols() via FFT.
    
    Parameters
    ----------
    refvals : ndarray
        Averaged column reference pixels
    data_shape : tuple
        Shape of original data (nz,ny,nx)
    perint : bool
        Smooth side reference pixel per int, otherwise per frame.
    edge_wrap : bool
        Add a partial frames to the beginning and end of each averaged
        time series pixels in order to get rid of edge effects.
    delt : float
        Time between reference pixel samples.
    savgol : bool
        Using Savitsky-Golay filter method rather than FFT.
    winsize : int
        Size of the window filter.
    order : int
        Order of the polynomial used to fit the samples.
    """
    #in perint=True, you are smoothing across frames and rows together,
    #like treating the entire cube’s ref signal as one long time-series.
    nz,ny,nx = data_shape
    if perint: # per integration, treats the entire (nz, ny) array as one flattened 1D series
        if edge_wrap: # Wrap around to avoid edge effects, "mirror" the first and last frames to reduce edge ringing:
            #These are stacked above and below refvals
            #After smoothing, will strip off these mirrored sections and reshape.
            refvals2 = np.vstack((refvals[0][::-1], refvals, refvals[-1][::-1]))
            if savgol: # SavGol filter
                refvals_smoothed2 = savgol_filter(refvals2.ravel(), winsize, order, delta=1)
            else: # Or "optimal" smoothing algorithm
                refvals_smoothed2 = smooth_fft(refvals2, delt)
            refvals_smoothed = refvals_smoothed2[ny:-ny].reshape(refvals.shape)
        else:
            if savgol:
                refvals_smoothed = savgol_filter(refvals.ravel(), winsize, order, delta=1)
            else:
                refvals_smoothed = smooth_fft(refvals, delt)
            refvals_smoothed = refvals_smoothed.reshape(refvals.shape)
    else: #smooth each frame’s row-series separately
        refvals_smoothed = []
        if edge_wrap: # Wrap around to avoid edge effects
            for ref in refvals: #(ny,)
                #mirror to handle FFT more gently on edges
                ref2 = np.concatenate((ref[:ny//2][::-1], ref, ref[ny//2:][::-1]))
                if savgol:
                    ref_smth = savgol_filter(ref2, winsize, order, delta=1)
                else:
                    ref_smth = smooth_fft(ref2, delt)
                refvals_smoothed.append(ref_smth[ny//2:ny//2+ny])
            refvals_smoothed = np.array(refvals_smoothed)
        else:
            for ref in refvals:
                if savgol:
                    ref_smth = savgol_filter(ref, winsize, order, delta=1)
                else:
                    ref_smth = smooth_fft(ref, delt)
                refvals_smoothed.append(ref_smth)
            refvals_smoothed = np.array(refvals_smoothed)
    return refvals_smoothed

def smooth_fft(data, delt, first_deriv=False, second_deriv=False):
    """Optimal smoothing algorithm
    Smoothing algorithm to perform optimal filtering of the
    vertical reference pixel to reduce 1/f noise (horizontal stripes),
    based on the Kosarev & Pantos algorithm. This assumes that the
    data to be filtered/smoothed has been sampled evenly.
    If first_deriv is set, then returns two results
    if second_deriv is set, then returns three results.
    Adapted from M. Robberto IDL code:
    http://www.stsci.edu/~robberto/Main/Software/IDL4pipeline/
    
    Parameters
    ----------
    data : ndarray
        Signal to be filtered.
    delt : float
        Delta time between samples.
    first_deriv : bool
        Return the first derivative.
    second_deriv : bool
        Return the second derivative (along with first).
    """

    Dat = data.flatten()
    N = Dat.size
    Pi2 = 2*np.pi
    OMEGA = Pi2 / (N*delt)
    X = np.arange(N) * delt
    ##------------------------------------------------
    ## Center and Baselinefit of the data
    ##------------------------------------------------
    Dat_m = Dat - np.mean(Dat) #data with its global mean removed
    SLOPE = (Dat_m[-1] - Dat_m[0]) / (N-2) #slope
    Dat_b = Dat_m - Dat_m[0] - SLOPE * X / delt #detrended, linear baseline removed
    ##------------------------------------------------
    ## Compute fft- / power- spectrum
    ##------------------------------------------------
    Dat_F = np.fft.rfft(Dat_b) #FFT
    Dat_P = np.abs(Dat_F)**2 #power spectrum
    ##------------------------------------------------
    ## Noise spectrum from 'half' to 'full'
    ## Mind: half means N/4, full means N/2
    ## assume that mid–high frequencies (from N/4 to N/2) are dominated by white noise, not signal.
    ## compute the average power in that band ==> Noise
    ## This is an estimate of the noise floor of the spectrum.
    ##------------------------------------------------
    i1 = int((N-1) / 4)
    i2 = int((N-1) / 2) + 1
    Sigma = np.sum(Dat_P[i1:i2])
    Noise = Sigma / ((N-1)/2 - (N-1)/4)
    ##------------------------------------------------
    ## Get Filtercoeff. according to Kosarev/Pantos
    ## Find the J0, start search at i=1 (i=0 is the mean), where the signal falls into the noise
    ##------------------------------------------------
    J0 = 2
    for i in np.arange(1, int(N/4)+1):
        sig0, sig1, sig2, sig3 = Dat_P[i:i+4]
        if (sig0<Noise) and ((sig1<Noise) or (sig2<Noise) or (sig3<Noise)):
            J0 = i
            break
    ##------------------------------------------------
    ## Compute straight line extrapolation to log(Dat_P)
    ##------------------------------------------------
    ii = np.arange(1,J0+1)
    logvals = np.log(Dat_P[1:J0+1])
    XY = np.sum(ii * logvals)
    XX = np.sum(ii**2)
    S  = np.sum(logvals)
    # Find parameters A1, B1
    XM = (2. + J0) / 2
    YM = S / J0
    A1 = (XY - J0*XM*YM) / (XX - J0*XM*XM)
    B1 = YM - A1 * XM
    # Compute J1, the frequency for which straight
    # line extrapolation drops 20dB below noise
    J1 = int(np.ceil((np.log(0.01*Noise) - B1) / A1 ))
    if J1<J0:
        J1 = J0+1
    ##------------------------------------------------
    ## Compute the Kosarev-Pantos filter windows
    ## Frequency-ranges: 0 -- J0 | J0+1 -- J1 | J1+1 -- N2
    ##------------------------------------------------
    nvals = int((N-1)/2 + 1)
    LOPT = np.zeros_like(Dat_P)
    LOPT[0:J0+1] = Dat_P[0:J0+1] / (Dat_P[0:J0+1] + Noise)
    i_arr = np.arange(J1-J0) + J0+1
    LOPT[J0+1:J1+1] = np.exp(A1*i_arr+B1) / (np.exp(A1*i_arr+B1) + Noise)
    ##--------------------------------------------------------------------
    ## De-noise the Spectrum with the filter
    ## Calculate the first and second derivative (i.e. multiply by iW)
    ##--------------------------------------------------------------------
    # first loop gives smoothed data
    # second loop produces first derivative
    # third loop produces second derivative
    if second_deriv:
        ndiff = 3
    elif first_deriv:
        ndiff = 2
    else:
        ndiff = 1

    for diff in range(ndiff):
        Fltr_Spectrum = np.zeros_like(Dat_P,dtype=complex)
        # make the filter complex
        i1 = 1; n2 = int((N-1)/2)+1; i2 = i1+n2
        FltrCoef = LOPT[i1:].astype(np.complex128)
        # differentitation in frequency domain
        iW = ((np.arange(n2)+i1)*OMEGA*1j)**diff
        # multiply spectrum with filter coefficient
        Fltr_Spectrum[i1:] = Dat_F[i1:] * FltrCoef * iW
        # Fltr_Spectrum[0] values
        # The derivatives of Fltr_Spectrum[0] are 0
        # Mean if diff = 0
        Fltr_Spectrum[0] = 0 if diff>0 else Dat_F[0]
        # Inverse fourier transform back in time domain
        Dat_T = np.fft.irfft(Fltr_Spectrum)
        #Dat_T[-1] = np.real(Dat_T[0]) + 1j*np.imag(Dat_T[-1])
        # This ist the smoothed time series (baseline added)
        if diff==0:
            Smoothed_Data = np.real(Dat_T) + Dat[0] + SLOPE * X / delt
        elif diff==1:
            First_Diff = np.real(Dat_T) + SLOPE / delt
        elif diff==2:
            Secnd_Diff = np.real(Dat_T)
    if second_deriv:
        return Smoothed_Data, First_Diff, Secnd_Diff
    elif first_deriv:
        return Smoothed_Data, First_Diff
    else:
        return Smoothed_Data  #return the original data, but with high-frequency noise stripped out,
                              #and only the low-frequency “shape” left, plus the original mean/trend.