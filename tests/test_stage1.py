from liger_iris_pipeline.pipeline import Stage1Pipeline
from liger_iris_pipeline import datamodels
from liger_iris_sim.utr.create_ramp import create_ramp
import numpy as np
import os
from liger_iris_pipeline.datamodels.dqflags import DQ_FLAGS

import matplotlib.pyplot as plt

def test_stage1(tmp_path):

    os.environ['KOA_CALIBRATION_CACHE'] = str(tmp_path) + '/KOA_CALIBRATION_CACHE/'

    # --- Define parameters for the simulated ramp ---
    max_cores = 2
    max_slope = 50  # e-/s
    readtime = 1.7  # seconds
    n_reads = 10
    ny, nx = 10, 10 # size of the detector

    # --- Non-linearity and its inverse polynomial coefficients ---

    # Create an ideal ramp (1D array for demonstration)
    ideal_ramp = np.linspace(0, np.iinfo(np.uint16).max, 1001, endpoint=True)
    nonlin_coeffs = [-1e-6, 1, 0]  # Example coefficients for a cubic non-linearity
    # nonlin_coeffs = [ 1, 0]  # Example coefficients for a cubic non-linearity
    nonlinear_ramp = np.polyval(nonlin_coeffs, ideal_ramp)

    # Fit inverse polynomial (correction) coefficients
    nonlin_correction_coefs = np.polyfit(nonlinear_ramp, ideal_ramp, deg=5)

    # Apply correction and check accuracy
    nonlin_corrected_ramp = np.polyval(nonlin_correction_coefs, nonlinear_ramp)

    coeffs = np.broadcast_to(nonlin_correction_coefs[::-1, None, None], (np.size(nonlin_correction_coefs), ny, nx))
    thresh = np.zeros(shape=(ny, nx), dtype=np.uint16)
    max = np.zeros(shape=(ny, nx), dtype=np.uint16)
    nonlin_model = datamodels.NonlinearCorrectionModel(
        coeffs=coeffs,
        nonlin_thresh=thresh,
        nonlin_max=max,
        instrument_name='Liger',
        meta={'instrument.mode': 'IMG'}
    )

    # --- Create DQ init map ---
    dqinit_map = np.zeros((ny, nx), dtype=np.uint32)
    
    # set row to bad
    dqinit_map[5, :] |= DQ_FLAGS["DO_NOT_USE"]
    dqinit_model = datamodels.DQModel(
        dq=dqinit_map,
        instrument_name='Liger',
        meta={'instrument.mode': 'IMG'}
    )

    # --- Create saturation threshold map ---
    saturation_threshold = np.iinfo(np.uint16).max  # DN
    saturation_map = np.full((ny, nx), saturation_threshold, dtype=np.uint16)
    saturation_model = datamodels.SaturationModel(
        sat_thresh=saturation_map,
        instrument_name='Liger',
        meta={'instrument.mode': 'IMG'}
    )
    
    # --- Create random gain map ---
    gain = 1.1  # e-/ADU
    gain_map = np.full((ny, nx), gain, dtype=np.float32)
    gain_model = datamodels.GainModel(
        gain=gain_map,
        cov=np.zeros((2, 2, ny, nx), dtype=np.float32),
        instrument_name='Liger',
        meta={'instrument.mode': 'IMG'}
    )

    # --- Create bias map ---
    bias = 1000 # e-
    bias_map = np.full((ny, nx), bias, dtype=np.float32)
    bias_model = datamodels.BiasModel(
        data=bias_map / gain_map,  # Bias DataModel in DN
        data_err=np.zeros_like(bias_map),
        ktc=np.zeros_like(bias_map),
        instrument_name='Liger',
        meta={'instrument.mode': 'IMG'}
    )

    # --- Create random read noise map ---
    RN = 5.0  # e- RMS
    rn_map = np.full((ny, nx), RN, dtype=np.float32)
    rn_model = datamodels.ReadNoiseModel(
        rn=rn_map / gain_map,  # read noise DataModel in DN RMS
        rn_err=np.zeros_like(rn_map),
        instrument_name='Liger',
        meta={'instrument.mode': 'IMG'}
    )

    # --- Create a fake UTR cube ---
    electron_rate_map = np.linspace(0, max_slope, nx, dtype=np.float32)[None, :] * np.ones((ny, 1), dtype=np.float32)
    ramp_data = create_ramp(
        electron_rate_map,  # in e-/s
        readtime=readtime, n_reads=n_reads,
        nonlin_coeffs=nonlin_coeffs, # ADU,
        gain=gain_map,  # in e-/ADU
        bias=bias_map,  # in e-
        kTC_noise=50,  # in e- RMS
        poisson_noise=False, read_noise=0,  # in e-/s
        convert_to_uint16=False, clip_ramps=True,
        max_cores=1
    )

    # Add a jump
    ramp_data['data'][4::,:,0:nx//2] += 1000

    ramp_model = datamodels.RampModel(
        instrument_name='Liger',
        data=np.abs(ramp_data['data']),
        dq_raw=ramp_data['dq_raw'],
        meta={**ramp_data['meta'], 'instrument.mode': 'IMG'}
    )
    ramp_model.meta.filename = "simulated_ramp.fits"
    
    # Step args
    steps = {
        'dq_init': {
            'dq': dqinit_model,
        },
        'sat_check': {
            'saturation': saturation_model,
        },
        'bias_sub': {
            'bias' : bias_model,
        },
        'nonlin_corr': {
            'nonlin': nonlin_model,
            'max_cores': max_cores,
        },
        'jump_det' : {
            'skip': False,
            'method': 'tpd',
            'max_cores': max_cores,
            'rejection_threshold': 4.0,
            'gain': gain_model,
            'rn': rn_model,
        },
        'ramp_fit' : {
            'method': 'cython_likely', # 'ols', 'mcds', 'cds', 'jwst_ols', 'jwst_likely', 'jwst_cython'
            'max_cores': max_cores,
            'jwst_jump_detection': False,
            'jwst_jump_rejection_threshold': 4.0,
            'gain': gain_model,
            'rn': rn_model,
        },
    }

    # Setup and call the stage 1 pipeline
    model_result = Stage1Pipeline.call(ramp_model, steps=steps)[0]

    # Test the result
    where_good = np.where(~(model_result.dq & np.full((ny, nx), DQ_FLAGS["DO_NOT_USE"])).astype(bool))
    
    np.testing.assert_allclose(
        model_result.data[where_good],
        electron_rate_map[where_good] / gain_map[where_good],
        rtol=1e-6, atol=1
    )