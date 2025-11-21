import drizzle
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS, DistortionLookupTable

def resample_distortion_drizzle(
    input_rate : np.ndarray,
    input_error : np.ndarray,
    input_dq : np.ndarray,
    itime : float,
    dx : np.ndarray,
    dy : np.ndarray,
) -> np.ndarray:
    
    size = input_rate.shape  # (ny, nx)

    # Input header for drizzle wcs
    hdr = fits.Header()
    hdr['NAXIS1'] = size[1]
    hdr['NAXIS2'] = size[0]

    # Exp time
    hdr['ITIME'] = itime  # Exposure time in seconds

    # Pixel-based coordinate system (all units in pixels)
    hdr['CRPIX1'] = size[1] / 2 + 1  # Reference pixel X (1-indexed)
    hdr['CRPIX2'] = size[0] / 2 + 1  # Reference pixel Y (1-indexed)
    hdr['CRVAL1'] = size[1] / 2 + 1  # Reference value X (pixels)
    hdr['CRVAL2'] = size[0] / 2 + 1  # Reference value Y (pixels)
    hdr['CDELT1'] = 1.0              # Pixel scale X (pixels/pixel)
    hdr['CDELT2'] = 1.0              # Pixel scale Y (pixels/pixel)
    hdr['CTYPE1'] = 'LINEAR'         # Linear coordinate type X
    hdr['CTYPE2'] = 'LINEAR'         # Linear coordinate type Y
    hdr['CUNIT1'] = 'pixel'          # Units for coordinate 1
    hdr['CUNIT2'] = 'pixel'          # Units for coordinate 2

    # Create WCS objects for input and output
    wcs_in = WCS(hdr)
    wcs_out = WCS(hdr)

    # Create distortion lookup tables
    xdist = DistortionLookupTable(dx.astype(np.float32), [0, 0], [0, 0], [1, 1])
    ydist = DistortionLookupTable(dy.astype(np.float32), [0, 0], [0, 0], [1, 1])
    wcs_in.cpdis1 = xdist
    wcs_in.cpdis2 = ydist

    # Calculate pixel mapping between input and output WCS
    pixmap = drizzle.utils.calc_pixmap(wcs_in, wcs_out)

    # Weights
    # NOTE: Confirm this is the right way to handle errors
    weight_map = np.where(
        input_error > 0,
        1.0 / input_error**2,
        0.0
    )

    # Set up drizzle resampling
    driz = drizzle.resample.Drizzle(
        kernel='square',
        out_shape=size, # Drizzle will crop to use only pixels always within bounding box
        fillval=0,
    )

    # Apply drizzle resampling to source image
    driz.add_image(
        input_rate,
        pixmap=pixmap,
        exptime=itime,
        #xmin=0,
        #xmax=0,
        #ymin=0,
        #ymax=0,
        weight_map=weight_map,
        in_units='cps' # counts per second
    )
    output_rate = driz.out_img
    output_error = np.where(driz.out_wht > 0, 1.0 / np.sqrt(driz.out_wht), np.inf)

    return output_rate, output_error