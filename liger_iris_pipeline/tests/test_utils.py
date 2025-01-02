import numpy as np
from astropy.time import Time
from liger_iris_pipeline import datamodels

def add_imager_wcs_axes(ra : float, dec : float, size : tuple[int, int], scale : float):
    meta = {
        'wcsinfo.crpix1': 0,
        'wcsinfo.crpix2': 0,

        'wcsinfo.crval1': ra - (size[0] / 2 - 0.5) * scale / 3600000,
        'wcsinfo.crval2': dec - (size[1] / 2 - 0.5) * scale / 3600000,
        
        'wcsinfo.ctype1': 'RA---TAN',
        'wcsinfo.ctype2': 'DEC--TAN',

        'wcsinfo.cunit1': 'deg',
        'wcsinfo.cunit2': 'deg',

        'wcsinfo.cdelt1': scale / 3600000,
        'wcsinfo.cdelt2': scale / 3600000,
    }
    return meta

def add_ifu_wcs_axes(ra : float, dec : float, size : tuple[int, int], scale : float, dw : float):
    meta = {
        'wcsinfo.crpix1': 0,
        'wcsinfo.crpix2': 0,

        'wcsinfo.crval1': ra - (size[0] / 2 - 0.5) * scale / 3600000,
        'wcsinfo.crval2': dec - (size[1] / 2 - 0.5) * scale / 3600000,
        
        'wcsinfo.ctype1': 'RA---TAN',
        'wcsinfo.ctype2': 'DEC--TAN',
        'wcsinfo.ctype3': '',

        'wcsinfo.cunit1': 'deg',
        'wcsinfo.cunit2': 'deg',
        'wcsinfo.cunit2': 'micron',

        'wcsinfo.cdelt1': scale / 3600000,
        'wcsinfo.cdelt2': scale / 3600000,
        'wcsinfo.cdelt3': dw
    }
    return meta

def get_default_metadata():
    meta = {}

    # CORE
    meta['origin']  = 'None'
    meta['filetype'] = 'FITS'
    meta['data_level'] = 1
    meta['drs_version'] = '0.0.1'

    # INSTRUMENT
    meta['instrument.era'] = '0.0.0'
    meta['instrument.pupil'] = 'ANY'
    meta['instrument.temp_imager_detector'] = 0.0
    meta['instrument.temp_ifu_detector'] = 0.0
    meta['instrument.temp_grating'] = 0.0

    # SUBARRAY
    meta['subarray.name'] = 'FULL'
    meta['subarray.id'] = 0
    meta['subarray.xstart'] = 1
    meta['subarray.ystart'] = 1
    meta['subarray.xsize'] = 4096
    meta['subarray.ysize'] = 4096
    meta['subarray.fastaxis'] = 0
    meta['subarray.slowaxis'] = 1
    meta['subarray.detxsiz'] = 4096
    meta['subarray.detysiz'] = 4096

    # TARGET
    meta['target.azimuth_start'] = 0.0
    meta['target.azimuth_middle'] = 0.0
    meta['target.azimuth_end'] = 0.0
    meta['target.equinox'] = 2000.0
    meta['target.type'] = 'FIXED'
    meta['target.ra_uncertainty'] = 0.0
    meta['target.dec_uncertainty'] = 0.0
    meta['target.proper_motion_ra'] = 0.0
    meta['target.proper_motion_dec'] = 0.0
    meta['target.proper_motion_epoch'] = 0.0
    meta['target.source_type'] = 'POINT'

    # EXPOSURE
    meta['exposure.type'] = 'SCI'
    meta['exposure.nreads'] = 1
    meta['exposure.ngroups'] = 1
    meta['exposure.group_gap_time'] = 0
    meta['exposure.nresets_at_start'] = 0
    meta['exposure.data_problem'] = False
    meta['exposure.number'] = 1
    meta['exposure.sequence_tot'] = 1
    meta['exposure.readmode'] = 'DEFAULT'
    return meta

def get_default_liger_metadata():
    meta = get_default_metadata()
    meta['organization']  = 'WMKO'
    meta['telescope'] = 'Keck-I'
    meta['instrument.name'] = 'Liger'
    meta['subarray.xsize'] = 2048
    meta['subarray.ysize'] = 2048
    meta['subarray.detxsiz'] = 2048
    meta['subarray.detysiz'] = 2048
    return meta

def get_default_iris_metadata():
    meta = get_default_metadata()
    meta['organization'] = 'TIO'
    meta['telescope'] = 'TMT'
    meta['instrument.name'] = 'IRIS'
    meta['subarray.xsize'] = 4096
    meta['subarray.ysize'] = 4096
    meta['subarray.detxsiz'] = 4096
    meta['subarray.detysiz'] = 4096
    return meta

def add_meta_data(model : datamodels.LigerIRISDataModel, meta : dict):

    # Instrument
    if meta['instrument.name'] == 'Liger':
        meta.update(get_default_liger_metadata())
    elif meta['instrument.name'] == 'IRIS':
        meta.update(get_default_iris_metadata())

    # Time
    time = Time(meta['exposure.jd_start'], format='jd')

    # CORE
    model.meta.date = time.isot
    model.meta.date_created = time.isot

    # EXPOSURE
    model.meta.exposure.date_start = time.datetime.strftime('%Y%m%d')
    model.meta.exposure.date_mid = time.datetime.strftime('%Y%m%d')
    model.meta.exposure.date_end = time.datetime.strftime('%Y%m%d')
    model.meta.exposure.time_start = time.datetime.strftime('%H:%M:%S.%f')[:-3]
    model.meta.exposure.time_mid = time.datetime.strftime('%H:%M:%S.%f')[:-3]
    model.meta.exposure.time_end = time.datetime.strftime('%H:%M:%S.%f')[:-3]

    # Target WCS
    if hasattr(model, 'data') and "Imager" in model.__class__.__name__:
        meta.update(add_imager_wcs_axes(ra=meta['target.ra'], dec=meta['target.dec'], size=model.data.shape, scale=meta['instrument.scale']))
    elif hasattr(model, 'data') and "IFU" in model.__class__.__name__:
        meta.update(add_ifu_wcs_axes(ra=meta['target.ra'], dec=meta['target.dec'], size=model.data.shape, scale=meta['instrument.scale']), dw=1)

    # Dict to object
    for key, value in meta.items():
        attrs = key.split('.')
        target = model.meta
        for attr in attrs[:-1]:
            if hasattr(target, attr):
                target = getattr(target, attr)
            else:
                target is None
        if target is not None:
            setattr(target, attrs[-1], value)

    return model


def create_ramp(
        source : np.ndarray, # e- / s / pixel including all sources
        meta : dict,
        readtime : float, # e- RMS
        n_reads_per_group : int, n_groups : int,
        nonlin_coeffs : np.ndarray | None = None,
    ):
    times = np.zeros(shape=(n_groups, n_reads_per_group), dtype=float)
    data = np.zeros(shape=(source.shape[0], source.shape[1], n_groups, n_reads_per_group), dtype=np.int16)
    dq = np.zeros(shape=(source.shape[0], source.shape[1], n_groups, n_reads_per_group), dtype=np.int16)
    for i in range(n_groups):
        for j in range(n_reads_per_group):
            t = (j + 1) * readtime
            image = data[:, :, i, j-1] + source * readtime
            if nonlin_coeffs is not None:
                image *= np.round(np.polyval(nonlin_coeffs[::-1], t).astype(np.int16))
            times[i, j] = t
            data[:, :, i, j] = image.copy()
    np.clip(data, 0, np.iinfo(np.int16).max)
    ramp_model = datamodels.RampModel(instrument=meta['instrument.name'], times=times, data=data, dq=dq)
    add_meta_data(ramp_model, meta)
    return ramp_model