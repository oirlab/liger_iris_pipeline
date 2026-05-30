from liger_iris_pipeline.pipeline import ProcessSatDetFlatsPipeline
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.datamodels import DQ_FLAGS
from liger_iris_sim.utr.create_ramp import create_ramp
import numpy as np


def test_stage1_sat_nonlin_calib(tmp_path):
    
    np.random.seed(12345)

    # --- Define parameters for the simulated ramp ---
    max_cores = 2
    max_slope = 1000  # e-/s
    readtime = 1.7  # seconds
    n_reads = 60
    N_files = 10  # number of simulated files to create
    ny, nx = 2,2  # size of the detector

    meta = {'instrument.name' : 'Liger', 'instrument.mode': 'IMG'}

    # --- Non-linearity and its inverse polynomial coefficients ---

    # Create an ideal ramp (1D array for demonstration)
    ideal_ramp = np.linspace(0, 1.5 * np.iinfo(np.uint16).max, 1001, endpoint=True)
    nonlin_coeffs = [-1e-6, 1, 0]  # Example coefficients for a cubic non-linearity
    # nonlin_coeffs = [1, 0]  # Example coefficients for a cubic non-linearity
    nonlinear_ramp = np.polyval(nonlin_coeffs, ideal_ramp)

    # Fit inverse polynomial (correction) coefficients
    #nonlin_correction_coefs = np.polyfit(nonlinear_ramp, ideal_ramp, deg=5)
    nonlin_correction_coefs = np.array([0.00000000e+00, 9.93166438e-01, 9.93459922e-07, 1.99687217e-12, 4.28159139e-18, 2.47963102e-23])[::-1]

    # Apply correction and check accuracy
    nonlin_corrected_ramp = np.polyval(nonlin_correction_coefs, nonlinear_ramp)

    coeffs = np.broadcast_to(nonlin_correction_coefs[::-1, None, None], (np.size(nonlin_correction_coefs), ny, nx))
    thresh = np.zeros(shape=(ny, nx), dtype=np.uint16)
    max = np.full(shape=(ny, nx), fill_value=0.9 * np.iinfo(np.uint16).max, dtype=np.uint16)
    nonlin_dq = np.zeros(shape=(ny, nx), dtype=np.uint32)
    nonlin_model = datamodels.NonlinearCorrectionModel(
        coeffs=coeffs,
        nonlin_thresh=thresh,
        nonlin_max=max,
        dq=nonlin_dq,
        meta=meta,
    )

    # --- Create DQ init map ---
    dqinit_map = np.zeros((ny, nx), dtype=np.uint32)
    # set row to bad
    # dqinit_map[5, :] |= DQ_FLAGS["DO_NOT_USE"]
    dqinit_model = datamodels.DQModel(dq=dqinit_map)

    # --- Create saturation threshold map ---
    saturation_threshold = np.iinfo(np.uint16).max  # DN
    saturation_map = np.full((ny, nx), saturation_threshold, dtype=np.float32)
    saturation_model = datamodels.SaturationModel(
        sat_thresh=saturation_map,
        meta=meta,
    )

    # --- Create random gain map ---
    gain = 1  # e-/ADU
    gain_map = np.full((ny, nx), gain, dtype=np.float32)
    gain_model = datamodels.GainModel(
        gain=gain_map,
        rn=np.full_like(gain_map, 0.0),
        cov=np.full((2, 2, ny, nx), 0, dtype=np.float32),
        meta=meta,
    )

    # --- Create random dark map ---
    # dark_current = 1  # e-/s
    # dark_map = np.random.normal(loc=dark_current, scale=dark_current / 10, size=(ny, nx)).astype(np.float32)
    dark_map = np.zeros((ny, nx), dtype=np.float32)
    dark_model = datamodels.DarkModel(
        data=dark_map / gain_map,  # dark in DN/s
        err=np.zeros_like(dark_map),
        meta=meta,
    )

    # --- Create bias map ---
    bias = 1000  # e-/s
    bias_map = np.full((ny, nx), bias, dtype=np.float32)
    kTC_noise = 0  # e-/s
    kTC_noise_map = np.full((ny, nx), kTC_noise, dtype=np.float32)
    bias_model = datamodels.BiasModel(
        data=bias_map / gain_map,  # bias in DN/s
        ktc=kTC_noise_map / gain_map,  # kTC in DN/s
        meta=meta,
    )

    # --- Create random flat map ---
    # detflat_map = np.random.normal(loc=1, scale=0.1, size=(ny, nx)).astype(np.float32)
    detflat_map = np.ones((ny, nx), dtype=np.float32)
    detflat_model = datamodels.DetectorFlatModel(
        data=detflat_map,
        err=np.full_like(gain_map, 0.3),
        meta=meta,
    )

    # --- Create random read noise map ---
    RN = 0.1  # e-
    rn_map = np.full((ny, nx), RN, dtype=np.float32)
    rn_model = datamodels.ReadNoiseModel(
        rn=rn_map / gain_map,
        rn_err=np.zeros_like(rn_map),
        meta=meta,
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
            kTC_noise=kTC_noise,  # in e-/s
            poisson_noise=False, read_noise=rn_map,  # in e-/s
            convert_to_uint16=True, clip_ramps=True,
            max_cores=max_cores
        )

        ramp_model = datamodels.RampModel(
            data=ramp_data['data'],
            dq_raw=ramp_data['dq_raw'],
            meta=ramp_data['meta']
        )

        ramp_model_sequence.append(ramp_model)

    pipe_max_cores = max_cores
    
    # --- Specify the step arguments here ---
    steps = {
        # 'register_saturation_cal':{
        #     'skip': True,
        # },
        'make_nonlin': {
            'mode': 'full_detector',
            'use_legendre': True,
            'order': 5,
            'readstart':0,
            'satval_frac': 0.95,
            'criterion_for_nonlin_thresh':0.01,
            'criterion_for_nonlin_max':0.05,
        },
        # 'register_nonlin_cal':{
        #     'skip': True,
        # },
        'bias_sub': {
            'skip': True,
        },
        # 'nonlin_corr': {
        #     'skip': True,
        # },
        # 'jump_det' : {
        #     'skip': True,
        #     'method': 'tpd',
        #     'rejection_threshold': 4.0,
        # },
        # 'ramp_fit' : {
        #     'skip': True,
        #     'method': 'cython_likely', # 'ols', 'mcds', 'cds', 'jwst_ols', 'jwst_likely', 'cython_likely'
        #     'max_cores': pipe_max_cores,
        #     'jwst_jump_detection': False,
        #     'jwst_jump_rejection_threshold': 4.0,
        # },
    }

    # Setup and call the stage 0 pipeline
    satflats_pipe = ProcessSatDetFlatsPipeline(steps=steps)

    # Set any step args

    satflats_pipe.dq_init.dq = dqinit_model
    satflats_pipe.sat_check.saturation = saturation_model
    satflats_pipe.bias_sub.bias = bias_model
    satflats_pipe.make_nonlin.gain = gain_model
    satflats_pipe.make_nonlin.rn = rn_model
    satflats_pipe.make_nonlin.saturation = saturation_model
    satflats_pipe.make_nonlin.bias = bias_model

    # Run pipeline
    model_result = satflats_pipe.run(ramp_model_sequence)

    np.testing.assert_allclose(model_result['saturation'].sat_thresh, 65435, rtol=1e-6, atol=1)
    assert model_result['saturation'].sat_thresh.shape[0] == ny
    assert model_result['saturation'].sat_thresh.shape[1] == nx

    # print("nonlin full detector")
    # print(model_result['nonlin'].coeffs[:,0])
    # print(model_result['nonlin'].nonlin_thresh[0])
    # print(model_result['nonlin'].nonlin_max[0])
    # print(model_result['nonlin'].dq)

    import matplotlib.pyplot as plt

    nonlin_corrected_ramp_4testing = np.polyval(model_result['nonlin'].coeffs[::-1,0, 0], nonlinear_ramp)
    rel_err_ideal = (nonlin_corrected_ramp[1::] - ideal_ramp[1::]) / ideal_ramp[1::]
    rel_err_4testing = (nonlin_corrected_ramp_4testing[1::] - ideal_ramp[1::]) / ideal_ramp[1::]
    # print(np.abs(rel_err_ideal[1::] - rel_err_4testing[1::]))
    assert np.sum(np.abs(rel_err_ideal - rel_err_4testing) > 1e-2) == 0
    assert abs(int(model_result['nonlin'].nonlin_thresh[0, 0]) - 18000) < 500
    assert abs(int(model_result['nonlin'].nonlin_max[0, 0]) - 52600) < 500

    # Run pipeline
    steps['make_nonlin']['mode'] = 'per_pixel'
    satflats_pipe = ProcessSatDetFlatsPipeline(steps=steps)
    satflats_pipe.dq_init.dq = dqinit_model
    satflats_pipe.sat_check.saturation = saturation_model
    satflats_pipe.bias_sub.bias = bias_model
    satflats_pipe.make_nonlin.gain = gain_model
    satflats_pipe.make_nonlin.rn = rn_model
    satflats_pipe.make_nonlin.saturation = saturation_model
    satflats_pipe.make_nonlin.bias = bias_model
    model_result = satflats_pipe.run(ramp_model_sequence)

    # print("nonlin per_pixel")
    # print(model_result['nonlin'].coeffs.shape)
    # print(model_result['nonlin'].nonlin_thresh)
    # print(model_result['nonlin'].nonlin_max)
    # print(model_result['nonlin'].dq)

    nonlin_corrected_ramp_4testing = np.polyval(model_result['nonlin'].coeffs[::-1, 0, 0], nonlinear_ramp)
    rel_err_ideal = (nonlin_corrected_ramp[1::] - ideal_ramp[1::]) / ideal_ramp[1::]
    rel_err_4testing = (nonlin_corrected_ramp_4testing[1::] - ideal_ramp[1::]) / ideal_ramp[1::]
    # print(np.abs(rel_err_ideal[1::] - rel_err_4testing[1::]))
    assert np.sum(np.abs(rel_err_ideal - rel_err_4testing) > 1e-2) == 0
    assert abs(int(model_result['nonlin'].nonlin_thresh[0, 0]) - 18000) < 500
    assert abs(int(model_result['nonlin'].nonlin_max[0, 0]) - 52600) < 500