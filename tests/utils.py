import numpy as np
from liger_iris_pipeline import datamodels

def make_imager_model(
    instrument_name='Liger',
    shape=(2048, 2048),
    snr=100,
    read_noise=1.0,
    meta=None,
):
    snr2 = snr**2
    rn2 = read_noise**2

    lam = 0.5 * (snr2 + np.sqrt(snr2**2 + 4 * snr2 * rn2))

    data = np.random.poisson(lam, size=shape).astype(np.float32)
    data += np.random.normal(0, read_noise, size=shape).astype(np.float32)

    var_rnoise = np.full(shape, rn2, dtype=np.float32)
    var_poisson = np.full(shape, lam, dtype=np.float32)

    err = np.sqrt(var_poisson + var_rnoise).astype(np.float32)

    if meta is None:
        meta = {}
    meta.setdefault('data_level', '1')

    return datamodels.ImagerModel(
        data=data,
        err=err,
        var_rnoise=var_rnoise,
        var_poisson=var_poisson,
        dq=np.zeros(shape, dtype=np.uint32),
        instrument_name=instrument_name,
        meta=meta,
    )


# def make_science_imager_model(
#     instrument_name: str = 'Liger',
#     shape: tuple[int, int] = (2048, 2048),
#     snr: float = 100,
#     meta : dict | None = None,
# ):
#     # Input rate
#     if meta is not None and 'exposure.exposure_time' in meta:
#         exposure_time = meta['exposure.exposure_time']
#     else:
#         exposure_time = 100.0  # s

#     rate = snr**2 / exposure_time

#     # Total counts per pixel
#     total_counts = np.random.poisson(rate * exposure_time, size=shape)
#     data = (total_counts / exposure_time).astype(np.float32)
#     err = np.sqrt(total_counts / exposure_time**2).astype(np.float32)
#     science_model = datamodels.ImagerModel(
#         data=data,
#         err=err,
#         dq=np.zeros(shape, dtype=np.uint32),
#         instrument_name=instrument_name,
#         meta=meta
#     )
#     science_model.meta.exposure.exposure_time = exposure_time
#     return science_model

# def make_dark_model(
#     instrument_name: str = "Liger",
#     shape : tuple[int, int] = (2048, 2048),
#     dark_current: float = 0.01,  # counts / s
#     snr: float = 100,
#     meta : dict | None = None,
# ):
#     exposure_time = snr**2 / dark_current  # s

#     # total dark counts per pixel
#     total_counts = np.random.poisson(dark_current * exposure_time, size=shape)
#     data = (total_counts / exposure_time).astype(np.float32)
#     err = np.sqrt(total_counts / exposure_time**2).astype(np.float32)

#     if meta is None:
#         meta = {}

#     dark_model = datamodels.DarkModel(
#         data=data,
#         err=err,
#         dq=np.zeros(shape, dtype=np.uint32),
#         instrument_name=instrument_name,
#         meta=meta,
#     )
#     dark_model.meta.exposure.exposure_time = exposure_time
#     return dark_model

# def make_detector_flat_model(
#     instrument_name: str = "Liger",
#     shape: tuple[int, int] = (2048, 2048),
#     snr: float = 100,
#     meta : dict | None = None,
# ):
#     exposure_time = snr**2

#     # total counts per pixel
#     total_counts = np.random.poisson(exposure_time, size=shape)
#     data = (total_counts / exposure_time).astype(np.float32)
#     err = np.sqrt(total_counts / exposure_time**2).astype(np.float32)

#     flat_model = datamodels.DetectorFlatModel(
#         data=data,
#         err=err,
#         dq=np.zeros(shape, dtype=np.uint32),
#         instrument_name=instrument_name,
#         meta=meta
#     )
#     flat_model.meta.exposure.exposure_time = exposure_time
#     return flat_model

from liger_iris_sim.sources import make_point_source_image

def make_star_field_imager(
    shape : tuple[int, int],
    psf : np.ndarray,
    n_stars = 1000,
    snr_range = (50, 200),
    peak_snr : bool = True,
):
    xdet = np.random.uniform(50, shape[1] - 50, n_stars).astype(int)
    ydet = np.random.uniform(50, shape[0] - 50, n_stars).astype(int)
    snr = np.random.uniform(snr_range[0], snr_range[1], n_stars)
    flux = snr**2
    star_image = make_point_source_image(
        xdet, ydet, flux, psf, shape,
        peak_flux=peak_snr
    )
    return dict(
        data=star_image,
        xdet=xdet, ydet=ydet, snr=snr,
        flux=flux,
    )