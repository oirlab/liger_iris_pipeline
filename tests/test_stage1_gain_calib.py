from liger_iris_pipeline.pipeline import ProcessDetFlatsPipeline
from liger_iris_pipeline import datamodels
from liger_iris_sim.utr.create_ramp import create_ramp
import numpy as np

def test_stage1_gain_calib(tmp_path):
    np.random.seed(12345)

    # --- Define parameters for the simulated ramp ---
    max_cores = 1
    max_slope = 200  # e-/s
    readtime = 1.7  # seconds
    n_reads = 30
    N_files = 100  # number of simulated files to create
    ny, nx = 2, 2  # size of the detector

    meta = {'instrument.name': 'Liger', 'instrument.mode': 'IMG'}

    # --- Non-linearity and its inverse polynomial coefficients ---
    ideal_ramp = np.linspace(0, 1.5 * np.iinfo(np.uint16).max, 1001, endpoint=True)
    nonlin_coeffs = [1, 0]  # Example coefficients for a cubic non-linearity
    nonlinear_ramp = np.polyval(nonlin_coeffs, ideal_ramp)
    nonlin_correction_coefs = np.polyfit(nonlinear_ramp, ideal_ramp, deg=5)
    print("Fitted correction coefficients:", nonlin_correction_coefs)

    coeffs = np.broadcast_to(nonlin_correction_coefs[::-1, None, None], (np.size(nonlin_correction_coefs), ny, nx))
    thresh = np.zeros(shape=(ny, nx), dtype=np.uint16)
    max = np.full(shape=(ny, nx), fill_value=0.9 * np.iinfo(np.uint16).max, dtype=np.uint16)
    nonlin_model = datamodels.NonlinearCorrectionModel(
        coeffs=coeffs,
        nonlin_thresh=thresh,
        nonlin_max=max,
        dq=np.zeros((ny, nx), dtype=np.uint32),
        meta=meta
    )

    # --- Create DQ init map ---
    dqinit_map = np.zeros((ny, nx), dtype=np.uint32)
    dqinit_model = datamodels.DQModel(dq=dqinit_map, meta=meta)

    # --- Create saturation threshold map ---
    saturation_threshold = np.iinfo(np.uint16).max  # DN
    saturation_map = np.full((ny, nx), saturation_threshold, dtype=np.float32)
    saturation_model = datamodels.SaturationModel(
        sat_thresh=saturation_map,
        meta=meta
    )

    # --- Create random gain map ---
    gain = 3  # e-/ADU
    gain_map = np.full((ny, nx), gain, dtype=np.float32)
    gain_model = datamodels.GainModel(
        gain=gain_map,
        rn=np.full_like(gain_map, 0.0),
        cov=np.full((2, 2, ny, nx), 0, dtype=np.float32),
        meta=meta
    )

    # --- Create random dark map ---
    dark_map = np.ones((ny, nx), dtype=np.float32)
    dark_model = datamodels.DarkModel(
        data=dark_map / gain_map,  # dark in DN/s
        err=np.zeros_like(dark_map),
        meta=meta
    )

    # --- Create bias map ---
    bias = 1000  # e-/s
    bias_map = np.full((ny, nx), bias, dtype=np.float32)
    bias_model = datamodels.BiasModel(
        data=bias_map / gain_map,  # bias in DN
        err=np.zeros_like(bias_map),
        meta=meta
    )

    # --- Create random flat map ---
    detflat_map = np.ones((ny, nx), dtype=np.float32)
    detflat_model = datamodels.DetectorFlatModel(
        data=detflat_map,
        err=np.full_like(gain_map, 0.03),
        meta=meta
    )

    # --- Create random read noise map ---
    RN = 8.5  # e-
    rn_map = np.full((ny, nx), RN, dtype=np.float32)
    rn_model = datamodels.ReadNoiseModel(
        rn=rn_map / gain_map,
        rn_err=np.ones_like(rn_map),
        meta=meta
    )

    # --- Create a fake UTR cube ---
    electron_rate_map = np.full((ny, nx), max_slope, dtype=np.float32)
    ramp_model_sequence = []
    for k in range(N_files):
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
            max_cores=max_cores
        )

        ramp_model = datamodels.RampModel(
            data=ramp_data['data'],
            dq_raw=ramp_data['dq_raw'],
            meta={**meta, **ramp_data['meta']}
        )
        ramp_model.meta.filename = "simulated_ramp.fits"

        ramp_model_sequence.append(ramp_model)

    # --- Specify the pipeline steps and arguments ---
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
        'make_gain': {
            'skip': False,
            'max_cores': max_cores,
            'mode': 'per_pixel',  # 'full_detector', 'per_pixel'
            'method': 'quad',
            'fix_RN': True,
            'init_delta_RN_start': -10,
            'init_delta_RN_step': 0.1,
            'init_delta_RN_stop': 10,
            'init_delta_gain_start': -0.5,
            'init_delta_gain_step': 0.05,
            'init_delta_gain_stop': 0.5,
            'quad_delta_gain': 0.2,
            'quad_delta_RN': 0.5,
            'init_gain': gain_model,
            'init_RN': rn_model,
        },
        'ramp_fit': {
            'skip': False,
            'gain': gain_model,
            'rn': rn_model,
        },
        'dark_sub': {
            #'skip': True,
            'dark': dark_model,
        },
        'gain': {
            #'skip': True,
            'gain': gain_model,
        },
        'coadd_frames': {
            'skip': True,
        },
        'make_detflat': {
            'skip': True,
        },
    }

    # Setup and call the stage 0 pipeline
    detflat_pipe = ProcessDetFlatsPipeline(steps=steps)

    # Run pipeline
    model_result = detflat_pipe.run(ramp_model_sequence)
    rel_residuals = np.abs(model_result['gain'].gain - gain_model.gain) / np.sqrt(
        model_result['gain'].cov[0, 0, :, :])
    assert np.sum(rel_residuals > 5) == 0

    # Test fix_RN = False
    steps['make_gain']['fix_RN'] = False
    detflat_pipe = ProcessDetFlatsPipeline(steps=steps)
    model_result = detflat_pipe.run(ramp_model_sequence)
    rel_residuals = np.abs(model_result['gain'].gain - gain_model.gain) / np.sqrt(
        model_result['gain'].cov[0, 0, :, :])
    assert np.sum(rel_residuals > 5) == 0

    # Test full_detector mode with quad method
    steps['make_gain']['fix_RN'] = False
    steps['make_gain']['mode'] = 'full_detector'
    steps['make_gain']['method'] = 'quad'
    detflat_pipe = ProcessDetFlatsPipeline(steps=steps)
    model_result = detflat_pipe.run(ramp_model_sequence)
    rel_residuals = np.abs(model_result['gain'].gain - gain_model.gain) / np.sqrt(
        model_result['gain'].cov[0, 0, :, :])
    assert np.sum(rel_residuals > 5) == 0

    # Test full_detector mode with grid method
    steps['make_gain']['fix_RN'] = False
    steps['make_gain']['mode'] = 'full_detector'
    steps['make_gain']['method'] = 'grid'
    detflat_pipe = ProcessDetFlatsPipeline(steps=steps)
    model_result = detflat_pipe.run(ramp_model_sequence)
    rel_residuals = np.abs(model_result['gain'].gain - gain_model.gain) / np.sqrt(
        model_result['gain'].cov[0, 0, :, :])
    assert np.sum(rel_residuals > 5) == 0

    # Test full_detector mode with both method
    steps['make_gain']['fix_RN'] = False
    steps['make_gain']['mode'] = 'full_detector'
    steps['make_gain']['method'] = 'both'
    detflat_pipe = ProcessDetFlatsPipeline(steps=steps)
    model_result = detflat_pipe.run(ramp_model_sequence)
    rel_residuals = np.abs(model_result['gain'].gain - gain_model.gain) / np.sqrt(
        model_result['gain'].cov[0, 0, :, :])
    assert np.sum(rel_residuals > 5) == 0

    # Test per_pixel mode with both method
    steps['make_gain']['fix_RN'] = False
    steps['make_gain']['mode'] = 'per_pixel'
    steps['make_gain']['method'] = 'both'
    steps['make_gain']['max_cores'] = 2
    detflat_pipe = ProcessDetFlatsPipeline(steps=steps)
    model_result = detflat_pipe.run(ramp_model_sequence)
    rel_residuals = np.abs(model_result['gain'].gain - gain_model.gain) / np.sqrt(
        model_result['gain'].cov[0, 0, :, :])
    assert np.sum(rel_residuals > 5) == 0


def test_stage1_gain_calib_stats(tmp_path):
    np.random.seed(12345)

    # --- Define parameters for the simulated ramp ---
    max_cores = 1
    max_slope = 200  # e-/s
    readtime = 1.7  # seconds
    n_reads = 30
    N_files = 100  # number of simulated files to create
    ny, nx = 10, 10  # size of the detector

    meta = {'instrument.name': 'Liger', 'instrument.mode': 'IMG'}

    # --- Non-linearity and its inverse polynomial coefficients ---
    ideal_ramp = np.linspace(0, 1.5 * np.iinfo(np.uint16).max, 1001, endpoint=True)
    nonlin_coeffs = [1, 0]  # Example coefficients for a cubic non-linearity
    nonlinear_ramp = np.polyval(nonlin_coeffs, ideal_ramp)
    nonlin_correction_coefs = np.polyfit(nonlinear_ramp, ideal_ramp, deg=5)
    print("Fitted correction coefficients:", nonlin_correction_coefs)

    coeffs = np.broadcast_to(nonlin_correction_coefs[::-1, None, None], (np.size(nonlin_correction_coefs), ny, nx))
    thresh = np.zeros(shape=(ny, nx), dtype=np.uint16)
    max = np.full(shape=(ny, nx), fill_value=0.9 * np.iinfo(np.uint16).max, dtype=np.uint16)
    nonlin_model = datamodels.NonlinearCorrectionModel(
        coeffs=coeffs,
        nonlin_thresh=thresh,
        nonlin_max=max,
        dq=np.zeros((ny, nx), dtype=np.uint32),
        meta=meta
    )

    # --- Create DQ init map ---
    dqinit_map = np.zeros((ny, nx), dtype=np.uint32)
    dqinit_model = datamodels.DQModel(dq=dqinit_map, meta=meta)

    # --- Create saturation threshold map ---
    saturation_threshold = np.iinfo(np.uint16).max  # DN
    saturation_map = np.full((ny, nx), saturation_threshold, dtype=np.float32)
    saturation_model = datamodels.SaturationModel(
        sat_thresh=saturation_map,
        meta=meta
    )

    # --- Create random gain map ---
    gain = 3  # e-/ADU
    gain_map = np.full((ny, nx), gain, dtype=np.float32)
    gain_model = datamodels.GainModel(
        gain=gain_map,
        rn=np.full_like(gain_map, 0.0),
        cov=np.full((2, 2, ny, nx), 0, dtype=np.float32),
        meta=meta
    )

    # --- Create random dark map ---
    dark_map = np.ones((ny, nx), dtype=np.float32)
    dark_model = datamodels.DarkModel(
        data=dark_map / gain_map,  # dark in DN/s
        err=np.zeros_like(dark_map),
        meta=meta
    )

    # --- Create bias map ---
    bias = 1000  # e-/s
    bias_map = np.full((ny, nx), bias, dtype=np.float32)
    bias_model = datamodels.BiasModel(
        data=bias_map / gain_map,  # bias in DN
        err=np.zeros_like(bias_map),
        meta=meta
    )

    # --- Create random flat map ---
    detflat_map = np.ones((ny, nx), dtype=np.float32)
    detflat_model = datamodels.DetectorFlatModel(
        data=detflat_map,
        err=np.full_like(gain_map, 0.03),
        meta=meta
    )

    # --- Create random read noise map ---
    RN = 8.5  # e-
    rn_map = np.full((ny, nx), RN, dtype=np.float32)
    rn_model = datamodels.ReadNoiseModel(
        rn=rn_map / gain_map,
        rn_err=np.ones_like(rn_map),
        meta=meta
    )

    # --- Create a fake UTR cube ---
    electron_rate_map = np.full((ny, nx), max_slope, dtype=np.float32)
    ramp_model_sequence = []
    for k in range(N_files):
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
            max_cores=max_cores
        )

        ramp_model = datamodels.RampModel(
            data=ramp_data['data'],
            dq_raw=ramp_data['dq_raw'],
            meta={**meta, **ramp_data['meta']}
        )
        ramp_model.meta.filename = "simulated_ramp.fits"

        ramp_model_sequence.append(ramp_model)

    # --- Specify the pipeline steps and arguments ---
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
        'make_gain': {
            'skip': False,
            'max_cores': max_cores,
            'mode': 'per_pixel',  # 'full_detector', 'per_pixel'
            'method': 'both',
            'fix_RN': False,
            'init_delta_RN_start': -10,
            'init_delta_RN_step': 0.1,
            'init_delta_RN_stop': 10,
            'init_delta_gain_start': -0.5,
            'init_delta_gain_step': 0.05,
            'init_delta_gain_stop': 0.5,
            'quad_delta_gain': 0.2,
            'quad_delta_RN': 0.5,
            'init_gain': gain_model,
            'init_RN': rn_model,
        },
        'ramp_fit': {
            #'skip': True,
            'gain': gain_model,
            'rn': rn_model,
        },
        'dark_sub': {
            #'skip': True,
            'dark': dark_model,
        },
        'gain': {
            #'skip': True,
            'gain': gain_model,
        },
        'coadd_frames': {
            'skip': True,
        },
        'make_detflat': {
            'skip': True,
        },
        # 'detflat': {
        #     'skip': True,
        # },
    }

    # Setup and call the stage 0 pipeline
    detflat_pipe = ProcessDetFlatsPipeline(steps=steps)

    # Run pipeline
    model_result = detflat_pipe.run(ramp_model_sequence)
    rel_residuals = np.abs(model_result['gain'].gain - gain_model.gain) / np.sqrt(
        model_result['gain'].cov[0, 0, :, :])
    assert np.sum(rel_residuals > 5) == 0

    # Check 1 sigma statistics of the gain residuals
    confidence_level = np.sum(rel_residuals < 1) / rel_residuals.size
    print(confidence_level)
    assert abs(confidence_level - 0.683) < 0.1