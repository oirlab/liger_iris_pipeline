# Imports
from liger_iris_pipeline.pipeline import Stage2ImagerPipeline
from liger_iris_pipeline import datamodels 
import numpy as np

from liger_iris_drp_resources import load_filters_summary
from liger_iris_sim.expose import expose_imager
from liger_iris_sim.utils import get_liger_psf
from liger_iris_sim.sky import get_maunakea_imager_sky_background

import matplotlib
matplotlib.use("QTAGG")
import matplotlib.pyplot as plt

from .utils import make_star_field_imager

def test_imager_stage2(tmp_path):

    np.random.seed(1)

    filter_name = "KN2"
    filter_info = load_filters_summary(filter_name)
    scale = 0.01  # arcsec / pixel
    
    psf, info = get_liger_psf(
        mode='img',
        xs=0, ys=0,
        wave=filter_info['wavecenter'],
        extend_powerlaw=True,
    )

    shape = (2048, 2048)
    star_data = make_star_field_imager(
        shape=shape,
        n_stars=1000,
        snr_range=(50, 200),
        psf=psf,
        peak_snr=True
    )

    sky_data = get_maunakea_imager_sky_background(
        filter_info=filter_info,
        plate_scale=scale,
    )

    # Total sky emission rate in photons / sec / pixel
    sky_em_bandpass = sky_data['sky_em_tot']
    sky_trans_bandpass = sky_data['sky_trans_mean']

    dark_current = 0.025  # electrons / sec / pixel
    dark_model = datamodels.DarkModel(
        data=np.full(shape, dark_current),
    )

    flat_val = 0.95
    flat_model = datamodels.DetectorFlatModel(
        data=np.full(shape, flat_val),
    )

    gain_val = 2.0
    gain_model = datamodels.GainModel(
        gain=np.full(shape, gain_val),
        cov=np.zeros((2, 2, *shape)),
    )

    sim_result = expose_imager(
        star_data['data'],
        sky_emission_rate=sky_em_bandpass,
        sky_trans_mean=sky_trans_bandpass,
        dark_current=dark_current,
    )

    meta = {
        'instrument.mode' : 'IMG',
        'instrument.filter': filter_name,
        'target.ra': 0.0,
        'target.dec': 0.0,
        'instrument.scale' : scale,
    }

    sci_model_L1 = datamodels.ImagerModel(
        data=sim_result['observed_rate'],
        err=sim_result['noise_rate'],
        meta=meta,
    )

    input = {
        "SCI": [sci_model_L1],
    }

    # Create and call the pipeline object
    steps = {
        'dark_sub' : {
            'dark' : dark_model,
        },
        'detflat' : {
            'detflat' : flat_model,
        },
        'gain_corr' : {
            'gain' : gain_model,
        },
        'background_sub' : {
            'do_scale_calc' : False,
        },
    }

    pipe = Stage2ImagerPipeline(steps=steps)
    sci_model_L2 = pipe.run(input)[0]

    # Manual L2 calculation
    bkg_model = datamodels.open(pipe.background_sub.background)
    ref_data = ((sci_model_L1.data - dark_model.data) * gain_model.gain) / flat_model.data - bkg_model.data
    np.testing.assert_allclose(sci_model_L2.data, ref_data, rtol=1e-6)