from liger_iris_pipeline.background import BackgroundSubtractionImagerStep, CalculateBackgroundImagerStep
import liger_iris_pipeline.datamodels as datamodels
import numpy as np

from liger_iris_sim.utils import get_psf
from liger_iris_drp_resources import load_filters_summary
from liger_iris_sim.sources import make_point_source_image
from liger_iris_sim.expose import expose_imager

def test_background_subtraction(tmp_path):

    np.random.seed(1)

    filter_name = "KN2"
    filter_info = load_filters_summary(filter_name)

    psf, info = get_psf(
        instrument_name='Liger',
        instrument_mode='img',
        xs=0, ys=0,
        wave=filter_info['wavecenter'],
        extend_powerlaw=True,
        output_plate_scale=0.01,
    )

    shape = (2048, 2048)
    n_stars = 1000
    peak_snr_range = (50, 200)
    xdet = np.random.uniform(50, shape[1] - 50, n_stars).astype(int)
    ydet = np.random.uniform(50, shape[0] - 50, n_stars).astype(int)
    snr = np.random.uniform(peak_snr_range[0], peak_snr_range[1], n_stars)
    flux_peak = snr**2
    flux_peak_mean = np.mean(flux_peak)
    image_base = np.zeros(shape, dtype=np.float64)
    make_point_source_image(
        xdet, ydet, flux_peak, psf, shape,
        peak_flux=True,
        image_out=image_base,
    )

    def make_background(
        shape,
        flux_peak_mean,
        bkg_contrast,
        bkg_grad_scale
    ):
        ny, nx = shape

        mid = bkg_contrast * flux_peak_mean
        left = mid * (1 - bkg_grad_scale)
        right = mid * (1 + bkg_grad_scale)

        x = np.linspace(0.0, 1.0, nx, dtype=np.float64)
        grad_1d = left + (right - left) * x

        bkg = np.tile(grad_1d, (ny, 1))
        return bkg
    
    # Average background contrast compared to peak star flux
    bkg_contrast = 0.02

    # Relative background scale factors for each image
    bkg_scales = np.array([0.5, 0.75, 1.0, 1.25, 1.5])

    # How much the background changes across the image
    bkg_grad_scale = 0.25
    
    sky_em = make_background(
        shape,
        flux_peak_mean,
        bkg_contrast,
        bkg_grad_scale
    )

    sci_models = []

    for s in bkg_scales:
        
        result = expose_imager(
            image_base,
            sky_emission_rate=sky_em * s
        )

        sci_model = datamodels.ImagerModel(
            data=result['observed_rate'],
            err=result['noise_rate'],
            var_poisson=np.zeros(shape),
            var_rnoise=np.zeros(shape),
            meta={
                'instrument.mode' : 'IMG',
                'instrument.filter': filter_name,
                'exposure.exposure_time': 1.0,
                'exposure.nframes': 1,
            }
        )
        sci_models.append(sci_model)

    step = CalculateBackgroundImagerStep()
    background_model = step.run(sci_models)
    scales_measured = step.bkg_result['scales']

    np.testing.assert_almost_equal(
        scales_measured,
        bkg_scales,
        decimal=1,
        err_msg="Sky scales do not match expected values."
    )

    for i in range(len(sci_models)):
        sci_models[i] = BackgroundSubtractionImagerStep.call(
            sci_models[i],
            background=background_model,
            scale=scales_measured[i]
        )