from liger_iris_pipeline.pipeline import Stage1Pipeline
from liger_iris_pipeline import datamodels
from liger_iris_sim.utr.create_ramp import create_ramp

import numpy as np
import os
from liger_iris_pipeline.datamodels import DQ_FLAGS

def test_stage1_ramp_fitting_readnoise_dominated(tmp_path):
    np.random.seed(12345)

    # --- Define parameters for the simulated ramp ---
    max_cores = 1
    max_slope = 0  # e-/s
    readtime = 1.7  # seconds
    n_reads = 30
    ny, nx = 100, 100 # size of the detector

    meta = {'instrument.name' : 'Liger', 'instrument.mode': 'IMG'}

    # --- Non-linearity and its inverse polynomial coefficients ---

    # Create an ideal ramp (1D array for demonstration)
    ideal_ramp = np.linspace(0, 1.5*np.iinfo(np.uint16).max, 1001, endpoint=True)
    # nonlin_coeffs = [-1e-6, 1, 0]  # Example coefficients for a cubic non-linearity
    nonlin_coeffs = [ 1, 0]  # Example coefficients for a cubic non-linearity
    nonlinear_ramp = np.polyval(nonlin_coeffs, ideal_ramp)

    # Fit inverse polynomial (correction) coefficients
    nonlin_correction_coefs = np.polyfit(nonlinear_ramp, ideal_ramp, deg=5)
    print("Fitted correction coefficients:", nonlin_correction_coefs)

    # Apply correction and check accuracy
    nonlin_corrected_ramp = np.polyval(nonlin_correction_coefs, nonlinear_ramp)

    coeffs = np.broadcast_to(nonlin_correction_coefs[::-1, None, None], (np.size(nonlin_correction_coefs), ny, nx))
    thresh = np.zeros(shape=(ny, nx), dtype=np.uint16)
    max = np.full(shape=(ny, nx),fill_value=0.9 * np.iinfo(np.uint16).max, dtype=np.uint16)
    nonlin_dq = np.zeros(shape=(ny,nx), dtype=np.uint32)
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
    gain = 3  # e-/ADU
    gain_map = np.full((ny, nx), gain, dtype=np.float32)
    gain_model = datamodels.GainModel(
        gain=gain_map,
        rn=np.full_like(gain_map, 0.0),
        cov=np.full((2, 2, ny, nx), 0, dtype=np.float32),
        meta=meta,
    )

    # --- Create random dark map ---
    dark_current = 0  # e-/s
    dark_map = np.random.normal(loc=dark_current, scale=dark_current / 10, size=(ny, nx)).astype(np.float32)
    dark_model = datamodels.DarkModel(
        data=dark_map / gain_map,  # dark in DN/s
        err=np.zeros_like(dark_map),
        meta=meta,
    )

    # --- Create bias map ---
    bias = 1000  # e-/s
    bias_map = np.full((ny, nx), bias, dtype=np.float32)
    kTC_noise = 50  # e-/s
    kTC_noise_map = np.full((ny, nx), kTC_noise, dtype=np.float32)
    bias_model = datamodels.BiasModel(
        data=bias_map / gain_map,  # bias in DN/s
        ktc=kTC_noise_map / gain_map,  # kTC in DN/s
        meta=meta,
    )

    # --- Create random flat map ---
    # detflat_map = np.random.normal(loc=1, scale=0.1, size=(ny, nx)).astype(np.float32)
    detflat_map = np.full((ny, nx), 1, dtype=np.float32)
    detflat_model = datamodels.DetectorFlatModel(
        data=detflat_map,
        err=np.zeros_like(detflat_map),
        meta=meta,
    )

    # --- Create random read noise map ---
    RN = 8.5  # e-
    rn_map = np.full((ny, nx), RN, dtype=np.float32)
    rn_model = datamodels.ReadNoiseModel(
        rn=rn_map / gain_map,
        rn_err=np.ones_like(rn_map),
        meta=meta,
    )

    methods = ['ols', 'mcds', 'cds', 'jwst_likely', 'cython_likely']
    
    for method in methods:
        
        # --- Create a fake UTR cube ---
        # electron_rate_map = np.linspace(0, max_slope, nx, dtype=np.float32)[None, :] * np.ones((ny, 1), dtype=np.float32)
        electron_rate_map = np.full((ny, nx), max_slope, dtype=np.float32)
        ramp_data = create_ramp(
            electron_rate_map,  # in e-/s
            readtime=readtime, n_reads=n_reads,
            nonlin_coeffs=nonlin_coeffs,
            gain=gain_map,  # in e-/s
            flat=detflat_map,
            dark=dark_map,  # in e-/s
            bias=bias_map,  # in e-/s
            kTC_noise=kTC_noise,  # in e-/s
            poisson_noise=True, read_noise=rn_map,  # in e-/s
            convert_to_uint16=False, clip_ramps=True,
            max_cores=max_cores,
        )

        #adding a jump
        # ramp_data['data'][4::,:,0:nx//2] += 1000

        ramp_model = datamodels.RampModel(
            data=ramp_data['data'],
            dq_raw=ramp_data['dq_raw'],
            meta={**meta, **ramp_data['meta']},
        )

        pipe_max_cores = max_cores
        # --- Specify the step arguments here ---
        steps = {
            'dq_init': {
                'skip': False,
            },
            'sat_check': {
                'skip': False,
            },
            'bias_sub': {
                'skip': False,
            },
            'nonlin_corr': {
                'skip': False,
            },
            'jump_det' : {
                'skip': True,
            },
            'ramp_fit' : {
                'skip': False,
                # 'method': method, # 'ols', 'mcds', 'cds', 'jwst_ols', 'jwst_likely', 'cython_likely'
                'max_cores': pipe_max_cores,
                'jwst_jump_detection': False,
                'jwst_jump_rejection_threshold': 4.0,
            },
        }

        steps["ramp_fit"]["method"] = method

        # Setup and call the stage 1 pipeline
        stage1_pipe = Stage1Pipeline(steps=steps, output_dir=str(tmp_path))

        # Set any step args
        stage1_pipe.dq_init.dq = dqinit_model
        stage1_pipe.sat_check.saturation = saturation_model
        stage1_pipe.bias_sub.bias = bias_model
        stage1_pipe.nonlin_corr.nonlin = nonlin_model
        stage1_pipe.ramp_fit.gain = gain_model
        stage1_pipe.ramp_fit.rn = rn_model

        # Run pipeline
        model_result = stage1_pipe.run(ramp_model)[0]  #

        where_good = np.where(~(model_result.dq & np.full((ny, nx), DQ_FLAGS["DO_NOT_USE"])).astype(bool))

        rel_residuals = np.abs(model_result.data[where_good] - electron_rate_map[where_good] / gain_map[where_good]) / model_result.err[where_good]

        print("Checking Method:", method)

        assert np.sum(rel_residuals > 10) == 0

        # Check 1 sigma statistics
        confidence_level = np.sum(rel_residuals < 1) / np.size(rel_residuals)

        assert abs(confidence_level-0.683)<0.15

def test_stage1_ramp_fitting_photon_dominated(tmp_path):
    np.random.seed(12345)

    # --- Define parameters for the simulated ramp ---
    max_cores = 1
    max_slope = 2000  # e-/s
    readtime = 1.7  # seconds
    n_reads = 100
    ny, nx = 100, 100 # size of the detector
    #ny, nx = 4096, 4096 # size of the detector

    meta = {'instrument.name' : 'Liger', 'instrument.mode': 'IMG'}

    # --- Non-linearity and its inverse polynomial coefficients ---

    # Create an ideal ramp (1D array for demonstration)
    ideal_ramp = np.linspace(0, 1.5*np.iinfo(np.uint16).max, 1001, endpoint=True)
    # nonlin_coeffs = [-1e-6, 1, 0]  # Example coefficients for a cubic non-linearity
    nonlin_coeffs = [ 1, 0]  # Example coefficients for a cubic non-linearity
    nonlinear_ramp = np.polyval(nonlin_coeffs, ideal_ramp)

    # Fit inverse polynomial (correction) coefficients
    nonlin_correction_coefs = np.polyfit(nonlinear_ramp, ideal_ramp, deg=5)
    print("Fitted correction coefficients:", nonlin_correction_coefs)

    # Apply correction and check accuracy
    nonlin_corrected_ramp = np.polyval(nonlin_correction_coefs, nonlinear_ramp)

    coeffs = np.broadcast_to(nonlin_correction_coefs[::-1, None, None], (np.size(nonlin_correction_coefs), ny, nx))
    thresh = np.zeros(shape=(ny, nx), dtype=np.uint16)
    max = np.full(shape=(ny, nx),fill_value=0.9 * np.iinfo(np.uint16).max, dtype=np.uint16)
    nonlin_dq = np.zeros(shape=(ny,nx), dtype=np.uint32)
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
    dqinit_model = datamodels.DQModel(dq=dqinit_map, meta=meta)

    # --- Create saturation threshold map ---
    saturation_threshold = np.iinfo(np.uint16).max  # DN
    saturation_map = np.full((ny, nx), saturation_threshold, dtype=np.float32)
    saturation_model = datamodels.SaturationModel(
        sat_thresh=saturation_map,
        meta=meta,
    )

    # --- Create random gain map ---
    gain = 3  # e-/ADU
    gain_map = np.full((ny, nx), gain, dtype=np.float32)
    gain_model = datamodels.GainModel(
        gain=gain_map,
        rn=np.full_like(gain_map, 0.0),
        cov=np.full((2, 2, ny, nx), 0, dtype=np.float32),
        meta=meta,
    )

    # --- Create random dark map ---
    dark_current = 0  # e-/s
    dark_map = np.random.normal(loc=dark_current, scale=dark_current / 10, size=(ny, nx)).astype(np.float32)
    dark_model = datamodels.DarkModel(
        data=dark_map / gain_map,  # dark in DN/s
        err=np.zeros_like(dark_map),
        meta=meta,
    )

    # --- Create bias map ---
    bias = 1000  # e-/s
    bias_map = np.full((ny, nx), bias, dtype=np.float32)
    kTC_noise = 50  # e-/s
    kTC_noise_map = np.full((ny, nx), kTC_noise, dtype=np.float32)
    bias_model = datamodels.BiasModel(
        data=bias_map / gain_map,  # bias in DN/s
        ktc=kTC_noise_map / gain_map,  # kTC in DN/s
        meta=meta,
    )

    # --- Create random flat map ---
    # detflat_map = np.random.normal(loc=1, scale=0.1, size=(ny, nx)).astype(np.float32)
    detflat_map = np.full((ny, nx), 1, dtype=np.float32)
    detflat_model = datamodels.DetectorFlatModel(
        data=detflat_map,
        err=np.zeros_like(detflat_map),
        meta=meta,
    )

    # --- Create random read noise map ---
    RN = 8.5  # e-
    rn_map = np.full((ny, nx), RN, dtype=np.float32)
    rn_model = datamodels.ReadNoiseModel(
        rn=rn_map / gain_map,
        rn_err=np.ones_like(rn_map),
        meta=meta,
    )

    methods = ['ols', 'mcds', 'cds', 'single', 'jwst_fixsen', 'jwst_likely', 'cython_likely']

    for method in methods:
        
        # --- Create a fake UTR cube ---
        # electron_rate_map = np.linspace(0, max_slope, nx, dtype=np.float32)[None, :] * np.ones((ny, 1), dtype=np.float32)
        electron_rate_map = np.full((ny, nx), max_slope, dtype=np.float32)

        ramp_data = create_ramp(
            electron_rate_map,  # in e-/s
            readtime=readtime, n_reads=n_reads,
            nonlin_coeffs=nonlin_coeffs,
            gain=gain_map,  # in e-/s
            flat=detflat_map,
            dark=dark_map,  # in e-/s
            bias=bias_map,  # in e-/s
            kTC_noise=kTC_noise,  # in e-/s
            poisson_noise=True, read_noise=rn_map,  # in e-/s
            convert_to_uint16=False, clip_ramps=True,
            max_cores=max_cores,
            n_channels=1,
        )

        #adding a jump
        # ramp_data['data'][4::,:,0:nx//2] += 1000

        ramp_model = datamodels.RampModel(
            data=ramp_data['data'],
            dq_raw=ramp_data['dq_raw'],
            meta={**meta, **ramp_data['meta']},
        )

        # Find first last in ramp_model.data[i, y, x] < 65535 (saturation threshold), set single_read_num to that read number minus 1 (to get the last good read)
        single_read_num = int(np.max(np.where(ramp_model.data < np.iinfo(np.uint16).max)[0])) - 1

        pipe_max_cores = max_cores
        # --- Specify the step arguments here ---
        steps = {
            'dq_init': {
                'skip': False,
            },
            'sat_check': {
                'skip': False,
            },
            'bias_sub': {
                'skip': False,
                # 'save_result':True,
                # # 'output_path': os.path.join(tmp_path,"bias_subtracted2.fits"),
                # 'output_dir': tmp_path,
            },
            'nonlin_corr': {
                'skip': False,
            },
            'jump_det' : {
                'skip': True,
                'method': 'jwst',
                'rejection_threshold': 4.0,
            },
            'ramp_fit' : {
                'skip': False,
                # 'method': method, # 'ols', 'mcds', 'cds', 'jwst_ols', 'jwst_likely', 'cython_likely'
                'max_cores': pipe_max_cores,
                'jwst_jump_detection': False,
                'jwst_jump_rejection_threshold': 4.0,
                'single_read_num': single_read_num,  # second to last read
            },
        }

        steps["ramp_fit"]["method"] = method

        # Setup and call the stage 1 pipeline
        stage1_pipe = Stage1Pipeline(steps=steps)

        # Set any step args
        stage1_pipe.dq_init.dq = dqinit_model
        stage1_pipe.sat_check.saturation = saturation_model
        stage1_pipe.bias_sub.bias = bias_model
        stage1_pipe.nonlin_corr.nonlin = nonlin_model
        stage1_pipe.ramp_fit.gain = gain_model
        stage1_pipe.ramp_fit.rn = rn_model

        # Run pipeline
        model_result = stage1_pipe.run(ramp_model)[0]  #

        where_good = np.where(~(model_result.dq & np.full((ny, nx), DQ_FLAGS["DO_NOT_USE"])).astype(bool))

        rel_residuals = np.abs(model_result.data[where_good] - electron_rate_map[where_good] / gain_map[where_good]) / model_result.err[where_good]

        assert np.sum(rel_residuals > 10) == 0

        # Check 1 sigma statistics
        confidence_level = np.sum(rel_residuals < 1) / np.size(rel_residuals)

        assert abs(confidence_level-0.683)<0.05