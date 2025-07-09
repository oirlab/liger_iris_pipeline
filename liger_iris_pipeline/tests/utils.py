import numpy as np
import astropy.time
from liger_iris_pipeline import datamodels

def get_imager_wcs_meta(model : datamodels.ImagerModel):
    model.meta.wcsinfo.crpix1 = 0
    model.meta.wcsinfo.crpix2 = 0
    model.meta.wcsinfo.crval1 = model.meta.target.ra - (model.shape[0] / 2 - 0.5) * model.meta.instrument.scale / 3600
    model.meta.wcsinfo.crval2 = model.meta.target.dec - (model.shape[1] / 2 - 0.5) * model.meta.instrument.scale / 3600
    model.meta.wcsinfo.ctype1 = 'RA---TAN'
    model.meta.wcsinfo.ctype2 = 'DEC--TAN'
    model.meta.wcsinfo.cunit1 = 'deg'
    model.meta.wcsinfo.cunit2 = 'deg'
    model.meta.wcsinfo.cdelt1 = model.meta.instrument.scale / 3600
    model.meta.wcsinfo.cdelt2 = model.meta.instrument.scale / 3600
    return model


def get_ifu_wcs_meta(model : datamodels.IFUCubeModel):
    model.meta.wcsinfo.crpix1 = 0
    model.meta.wcsinfo.crpix2 = 0
    model.meta.wcsinfo.crpix3 = 0
    model.meta.wcsinfo.crval1 = model.meta.target.ra - (model.shape[0] / 2 - 0.5) * model.meta.instrument.scale / 3600
    model.meta.wcsinfo.crval2 = model.meta.target.dec - (model.shape[1] / 2 - 0.5) * model.meta.instrument.scale / 3600
    model.meta.wcsinfo.crval3 = model.wave[0]
    model.meta.wcsinfo.ctype1 = 'RA---TAN'
    model.meta.wcsinfo.ctype2 = 'DEC--TAN'
    model.meta.wcsinfo.ctype3 = 'WAVE'
    model.meta.wcsinfo.cunit1 = 'deg'
    model.meta.wcsinfo.cunit2 = 'deg'
    model.meta.wcsinfo.cunit2 = 'micron'
    model.meta.wcsinfo.cdelt1 = model.meta.instrument.scale / 3600
    model.meta.wcsinfo.cdelt2 = model.meta.instrument.scale / 3600
    model.meta.wcsinfo.cdelt3 = model.wave[2] - model.wave[1]
    return model
    

def get_exposure_meta(model : datamodels.LigerIRISDataModel) -> dict:
    if model.meta.exposure.jd_start is not None and model.meta.exposure.exposure_time is not None:
        model.meta.exposure.jd_mid = model.meta.exposure.jd_start + model.meta.exposure.exposure_time / (2 * 86400)
        model.meta.exposure.jd_end = model.meta.exposure.jd_start + model.meta.exposure.exposure_time / 86400
        model.meta.exposure.datetime_start = astropy.time.Time(model.meta.exposure.jd_start, format='jd').strftime('%Y%m%d%H%M%S')
        model.meta.exposure.datetime_mid = astropy.time.Time(model.meta.exposure.jd_mid, format='jd').strftime('%Y%m%d%H%M%S')
        model.meta.exposure.datetime_end = astropy.time.Time(model.meta.exposure.jd_end, format='jd').strftime('%Y%m%d%H%M%S')
    if model.meta.exposure.exposure_type is None:
        model.meta.exposure.exposure_type = 'SCI'
    if model.meta.exposure.nframes is None:
       model.meta.exposure.nframes = 1
    if model.meta.exposure.exposure_number is None:
        model.meta.exposure.exposure_number = 1
    if model.meta.exposure.readmode is None:
        model.meta.exposure.readmode = 'DEFAULT'
    return model


def get_subarray_meta(model):
    if model.shape is not None:
        if model.meta.subarray.id is None and model.meta.subarray.name is None:
            model.meta.subarray.name = 'FULL'
            model.meta.subarray.id = 0
        if model.meta.subarray.ystart is None:
            model.meta.subarray.ystart = 1
        if model.meta.subarray.xstart is None:
            model.meta.subarray.xstart = 1
        model.meta.subarray.ysize = model.shape[0]
        model.meta.subarray.xsize = model.shape[1]
        model.meta.subarray.detxsize = 4096 if model.meta.instrument.name.lower() == 'iris' else 2048
        model.meta.subarray.detysize = 4096 if model.meta.instrument.name.lower() == 'iris' else 2048
        model.meta.subarray.fastaxis = 0
        model.meta.subarray.slowaxis = 1
    return model


def load_filter_summary(filepath : str | None = None):
    if filepath is None:
        import importlib.resources
        filters_dir = importlib.resources.files("liger_iris_pipeline.data.filters")
        filepath = filters_dir / "filters_summary.txt"
    data = np.genfromtxt(filepath, dtype=None, names=True, delimiter=',', encoding='utf-8')
    out = {}
    for i, f in enumerate(data['filter']):
        out[f] = {key : data[key][i] for key in data.dtype.names}
    return out


def get_instrument_meta(model : datamodels.LigerIRISDataModel):
    if model.meta.instrument.detector is None:
        if isinstance(model, datamodels.ImagerModel):
            if model.meta.instrument.name.lower() == 'iris':
                model.meta.instrument.detector = 'IMG1'
            else:
                model.meta.instrument.detector = 'IMG'
        elif isinstance(model, (datamodels.IFUCubeModel, datamodels.IFUImageModel)):
            model.meta.instrument.detector = 'IFU'
        elif model.meta.instrument.mode.lower() in ('lenslet', 'slicer'):
            model.meta.instrument.detector = 'IFU'
        elif model.meta.instrument.mode.lower() == 'img':
            model.meta.instrument.detector = 'IMG'
        else:
            raise ValueError(f"Unknown model type {type(model)} to set instrument detector.")
    filter_data = load_filter_summary()
    model.meta.instrument.wave_min = filter_data[model.meta.instrument.filter]['wavemin']
    model.meta.instrument.wave_center = filter_data[model.meta.instrument.filter]['wavecenter']
    model.meta.instrument.wave_max = filter_data[model.meta.instrument.filter]['wavemax']
    return model


def get_meta(model : datamodels.LigerIRISDataModel, meta : dict | None = None):
    """
    Populate certain model metadata defaults for development and testing data for now.

    Args:
        model (datamodels.LigerIRISDataModel): The data model to update.
    """
    if meta is not None:
        update_model_meta(model, meta)

    # Telescope
    if model.meta.telescope is None:
        model.meta.telescope = 'TMT' if model.meta.instrument.name.lower() == 'iris' else 'Keck-I'

    # Instrument
    if model.meta.instrument.name is not None:
        get_instrument_meta(model)

    # Add exposure metadata
    get_exposure_meta(model)

    # Subarray
    if model.meta.instrument.detector.lower() in ('img', 'img1'):
        get_subarray_meta(model)

    # WCS
    if isinstance(model, datamodels.ImagerModel) and model.data is not None and model.meta.target.ra is not None and model.meta.target.dec is not None:
        get_imager_wcs_meta(model)
    elif isinstance(model, datamodels.IFUCubeModel) and model.data is not None and model.meta.target.ra is not None and model.meta.target.dec is not None:
        get_ifu_wcs_meta(model)

    # Reference models
    if isinstance(model, datamodels.ReferenceFileModel):
        model.meta.ref_type = model._ref_type
        if model.meta.ref_version is None:
            model.meta.ref_version = '0.0.1'
    return model


def update_model_meta(model, meta):
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


def create_ramp(
    source : np.ndarray, # e- / s / pixel including all sources
    readtime : float, # e- RMS
    n_reads_per_group : int, n_groups : int,
    read_noise : float = 0, first_read_noise : float | None = None,
    nonlin_coeffs : np.ndarray | None = None,
    poisson_noise : bool = True
) -> datamodels.RampModel:
    times = np.zeros(shape=(n_groups, n_reads_per_group), dtype=float)
    data = np.zeros(shape=(source.shape[0], source.shape[1], n_groups, n_reads_per_group), dtype=np.int16)
    dq = np.zeros(shape=(source.shape[0], source.shape[1], n_groups, n_reads_per_group), dtype=np.int16)
    data_poisson = np.zeros(shape=(source.shape[0], source.shape[1], n_groups, n_reads_per_group), dtype=float)
    if first_read_noise is None:
        first_read_noise = read_noise
    for i in range(n_groups):
        for j in range(n_reads_per_group):
            t = (j + 1) * readtime
            image_prev = data_poisson[:, :, i, j-1] if j > 0 else np.zeros_like(source) # Previous read without read noise
            image_new = image_prev + source * readtime # Add new read
            if poisson_noise:
                image_new = np.random.poisson(lam=image_new, size=source.shape)
            data_poisson[:, :, i, j] = image_new
            if j == 0 and first_read_noise > 0:
                image_new += np.random.normal(loc=0, scale=first_read_noise, size=source.shape)
            elif j > 0 and read_noise > 0:
                image_new += np.random.normal(loc=0, scale=read_noise, size=source.shape)
            times[i, j] = t
            if nonlin_coeffs is not None:
                image_new *= np.round(np.polyval(nonlin_coeffs[::-1], t).astype(np.int16))
            data[:, :, i, j] = image_new.astype(np.int16)
    np.clip(data, 0, np.iinfo(np.int16).max)
    ramp_model = datamodels.RampModel(times=times, data=data, dq=dq)
    ramp_model.meta.data_level = 0
    return ramp_model