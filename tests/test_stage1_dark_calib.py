from liger_iris_pipeline.pipeline import ProcessDarksPipeline
from liger_iris_pipeline import datamodels
from liger_iris_sim.utr.create_ramp import create_ramp
import numpy as np

def test_stage1_dark_calib(tmp_path):
    np.random.seed(12345)

    # Parameters
    max_cores = 1
    max_slope = 0  # e-/s
    readtime = 1.7  # seconds
    n_reads = 30
    n_frames = 10  # number of simulated frames to create
    ny, nx = 10,10  # size of the detector

    meta = {'instrument.name' : 'Liger', 'instrument.mode': 'IMG'}

    # Create Non-linearity Model
    ideal_ramp = np.linspace(0, 1.5 * np.iinfo(np.uint16).max, 1001, endpoint=True)
    nonlin_coeffs = [1, 0]  # Example coefficients for a cubic non-linearity
    nonlinear_ramp = np.polyval(nonlin_coeffs, ideal_ramp)
    nonlin_correction_coeffs = np.polyfit(nonlinear_ramp, ideal_ramp, deg=5)
    nonlin_correction_coeffs = np.broadcast_to(nonlin_correction_coeffs[::-1, None, None], (np.size(nonlin_correction_coeffs), ny, nx))
    nonlin_thresh = np.zeros(shape=(ny, nx), dtype=np.uint16)
    nonlin_max = np.full(shape=(ny, nx), fill_value=0.9 * np.iinfo(np.uint16).max, dtype=np.uint16)
    nonlin_model = datamodels.NonlinearCorrectionModel(
        coeffs=nonlin_correction_coeffs,
        nonlin_thresh=nonlin_thresh,
        nonlin_max=nonlin_max,
        dq=np.zeros((ny, nx), dtype=np.uint32), # Necessary since dq.shape != coeffs.shape
        meta=meta,
    )

    # Create DQ Init Map
    dqinit_map = np.zeros((ny, nx), dtype=np.uint32)
    dqinit_model = datamodels.DQModel(dq=dqinit_map, meta=meta)

    # Create Saturation Map
    saturation_threshold = np.iinfo(np.uint16).max  # DN
    saturation_map = np.full((ny, nx), saturation_threshold, dtype=np.float32)
    saturation_model = datamodels.SaturationModel(
        sat_thresh=saturation_map,
        meta=meta,
    )

    # Create Gain Map
    gain = 3  # e-/ADU
    gain_map = np.full((ny, nx), gain, dtype=np.float32)
    gain_model = datamodels.GainModel(
        gain=gain_map,
        rn=np.full_like(gain_map, 0.0),
        cov=np.full((2, 2, ny, nx), 0, dtype=np.float32),
        meta=meta,
    )

    # Create Dark Map
    dark_current = 5  # e-/s
    dark_map = np.random.normal(loc=dark_current, scale=dark_current / 10, size=(ny, nx)).astype(np.float32)
    dark_model = datamodels.DarkModel(
        data=dark_map / gain_map,
        err=np.zeros_like(dark_map),
        meta=meta,
    )

    # Create Bias Map
    bias = 1000
    bias_map = np.full((ny, nx), bias, dtype=np.float32)
    kTC_noise = 50  # e-/s
    kTC_noise_map = np.full((ny, nx), kTC_noise, dtype=np.float32)
    bias_model = datamodels.BiasModel(
        data=bias_map / gain_map,
        err=kTC_noise_map / gain_map,
        meta=meta,
    )

    # Create Flat Model
    detflat_map = np.ones((ny, nx), dtype=np.float32)
    detflat_model = datamodels.DetectorFlatModel(
        data=detflat_map,
        err=np.full_like(gain_map, 0.03),
        meta=meta,
    )

    # Create Read Noise Model
    RN = 8.5  # e-
    rn_map = np.full((ny, nx), RN, dtype=np.float32)
    rn_model = datamodels.ReadNoiseModel(
        rn=rn_map / gain_map,
        rn_err=np.ones_like(rn_map),
        meta=meta,
    )

    # --- Create a fake UTR cube ---
    electron_rate_map = np.full((ny, nx), max_slope, dtype=np.float32)
    ramp_model_sequence = []
    for k in range(n_frames):
        ramp_data = create_ramp(
            electron_rate_map,  # in e-/s
            readtime=readtime, n_reads=n_reads,
            nonlin_coeffs=nonlin_coeffs,
            gain=gain_map,  # in e-/s
            flat=detflat_map,
            dark=dark_map,  # in e-/s
            bias=bias_map,  # in e-/s
            kTC_noise=50,  # in e-/s
            poisson_noise=True, read_noise=rn_map,  # in e-/s
            convert_to_uint16=True, clip_ramps=True,
            max_cores=max_cores,
            n_channels=1
        )

        ramp_model = datamodels.RampModel(
            data=ramp_data['data'],
            dq_raw=ramp_data['dq_raw'],
            meta={**meta, **ramp_data['meta']}
        )
        ramp_model.meta.filename = "simulated_ramp.fits"

        ramp_model_sequence.append(ramp_model)

    steps = {
        'dq_init': {
            'skip': False,
            'dq': dqinit_model,
        },
        'sat_check': {
            'skip': False,
            'max_cores': max_cores,
            'saturation': saturation_model,
        },
        'bias_sub': {
            'skip': False,
            'bias': bias_model,
        },
        'nonlin_corr': {
            'skip': False,
            'max_cores': max_cores,
            'nonlin': nonlin_model,
        },
        'jump_det': {
            'skip': False,
            'method': 'tpd',
            'max_cores': max_cores,
            'rejection_threshold': 40.0,
            'gain': gain_model,
            'rn': rn_model,
        },
        'make_rn': {
            'skip': False,
            'max_cores': max_cores,
            'mode': 'per_pixel',  # 'full_detector', 'per_pixel'
            'method': 'both',
            'init_delta_RN_start': -10,
            'init_delta_RN_step': 0.1,
            'init_delta_RN_stop': 10,
            'quad_delta_RN': 0.5,
            'rn_init': rn_model,
            'gain': gain_model,
        },
        'ramp_fit' : {
            'skip': False,
            'method': 'jwst_likely', # 'ols', 'mcds', 'cds', 'jwst_ols', 'jwst_likely'
            'max_cores': max_cores,
            'jwst_jump_detection': False,
            'jwst_jump_rejection_threshold': 4.0,
            'gain': gain_model,
            'rn': rn_model,
        },
        'coadd_frames': {
            'skip': False,
            'method': 'mean',
            'do_sigma_clip': False,
            'error_calc': 'propagate',
        },
        'make_dark': {
            'skip': False,
            'max_cores': max_cores,
        },
        # 'dark_sub': {
        #     'skip': True,
        #     'dark': dark_model,
        # },
        # 'gain': {
        #     'skip': True,
        #     'gain': gain_model,
        # },
        # 'detflat': {
        #     'skip': True,
        #     'detflat': detflat_model,
        # },
    }

    import matplotlib.pyplot as plt

    # Setup and call the stage 0 pipeline
    dark_pipe = ProcessDarksPipeline(steps=steps)

    # Run pipeline
    result = dark_pipe.run(ramp_model_sequence)

    rel_residuals = np.abs(result['read_noise'].rn - rn_model.rn) / result['read_noise'].rn_err
    assert np.sum(rel_residuals > 5) == 0
    
    # Check 1 sigma statistics
    confidence_level = np.sum(rel_residuals < 1) / rel_residuals.size
    assert abs(confidence_level - 0.683) < 0.1

    rel_residuals = np.abs(result['dark'].data - dark_model.data) / result['dark'].err
    assert np.sum(rel_residuals > 5) == 0
    
    # Check 1 sigma statistics
    confidence_level = np.sum(rel_residuals < 1) / rel_residuals.size
    assert abs(confidence_level - 0.683) < 0.1