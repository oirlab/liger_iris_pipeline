from liger_iris_pipeline.pipeline import ProcessDetFlatsPipeline
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.datamodels import DQ_FLAGS
from liger_iris_sim.utr.create_ramp import create_ramp
import numpy as np

def test_stage1_flat_calib(tmp_path):
    
    np.random.seed(12345)

    # --- Define parameters for the simulated ramp ---
    max_cores = 1
    max_slope = 200  # e-/s
    readtime = 1.7  # seconds
    n_reads = 30
    N_files = 10  # number of simulated files to create
    ny, nx = 10, 10  # size of the detector

    meta = {'instrument.name' : 'Liger', 'instrument.mode': 'IMG'}

    # Create an ideal ramp (1D array for demonstration)
    ideal_ramp = np.linspace(0, 1.5 * np.iinfo(np.uint16).max, 1001, endpoint=True)
    nonlin_coeffs = [1, 0]
    nonlinear_ramp = np.polyval(nonlin_coeffs, ideal_ramp)

    # Fit inverse polynomial (correction) coefficients
    nonlin_correction_coefs = np.polyfit(nonlinear_ramp, ideal_ramp, deg=5)

    # Apply correction and check accuracy
    nonlin_corrected_ramp = np.polyval(nonlin_correction_coefs, nonlinear_ramp)

    coeffs = np.broadcast_to(nonlin_correction_coefs[::-1, None, None], (np.size(nonlin_correction_coefs), ny, nx))
    thresh = np.zeros(shape=(ny, nx), dtype=np.uint16)
    max = np.full(shape=(ny, nx), fill_value=0.9 * np.iinfo(np.uint16).max, dtype=np.uint16)
    nonlin_model = datamodels.NonlinearCorrectionModel(
        coeffs=coeffs,
        nonlin_thresh=thresh,
        nonlin_max=max,
        dq=np.zeros((ny, nx), dtype=np.uint32),
    )

    # --- Create DQ init map ---
    dqinit_map = np.zeros((ny, nx), dtype=np.uint32)
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
    dark_map = np.ones((ny, nx), dtype=np.float32)
    dark_model = datamodels.DarkModel(
        data=dark_map / gain_map,  # dark in DN/s
        err=np.zeros_like(dark_map),
        meta=meta,
    )

    # --- Create bias map ---
    bias = 1000  # e-/s
    bias_map = np.full((ny, nx), bias, dtype=np.float32)
    bias_model = datamodels.BiasModel(
        data=bias_map,
        ktc=np.zeros_like(bias_map),
        meta=meta,
    )

    # --- Create random flat map ---
    # detflat_map = np.random.normal(loc=1, scale=0.1, size=(ny, nx)).astype(np.float32)
    detflat_map = np.ones((ny, nx), dtype=np.float32)
    detflat_map[0, 0] = 0.7  # cold pixel
    detflat_map[0, 1] = 0.95
    detflat_map[0, 2] = 1.1
    detflat_map[0, 3] = 1.4
    detflat_model = datamodels.DetectorFlatModel(
        data=detflat_map,
        err=np.full_like(gain_map, 0.3),
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
        # adding a jump
        # ramp_data['data'][4::,:,:] += 1000
        # ramp_data['data'][10::,:,:] += 1000
        # ramp_data['data'][15::,:,:] += 1000
        # ramp_data['data'][20::,:,:] += 1000
        # ramp_data['data'][4::,5,5] += 3000

        ramp_model = datamodels.RampModel(
            ramp_data['data'],
            dq_raw=ramp_data['dq_raw'],
            meta={**ramp_data['meta'], **meta}
        )
        ramp_model.meta.filename = "simulated_ramp.fits"

        ramp_model_sequence.append(ramp_model)

    # --- Specify the step arguments here ---
    steps = {
        'dq_init': {
            'dq': dqinit_model,
        },
        'sat_check': {
            'saturation': saturation_model,
        },
        'bias_sub': {
            'bias': bias_model,
        },
        'nonlin_corr': {
            'nonlin': nonlin_model,
        },
        'jump_det': {
            'skip': True,
            'method': 'tpd',
            'rejection_threshold': 40.0,
            'gain': gain_model,
            'rn' : rn_model,
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
            'method': 'jwst_likely',
            'jwst_jump_detection': False,
            'jwst_jump_rejection_threshold': 4.0,
            'gain': gain_model,
            'rn': rn_model,
        },
        'dark_sub': {
            'dark': dark_model,
        },
        'gain': {
            'gain': gain_model,
        },
    }


    # Setup and call the stage 0 pipeline
    detflat_pipe = ProcessDetFlatsPipeline(steps=steps)
    model_result = detflat_pipe.run(ramp_model_sequence)

    assert model_result['detflat'].dq[0,0] & DQ_FLAGS['COLD']
    assert not (model_result['detflat'].dq[0, 1] & DQ_FLAGS['COLD'])
    assert not (model_result['detflat'].dq[0, 2] & DQ_FLAGS['COLD'])
    assert not (model_result['detflat'].dq[0, 3] & DQ_FLAGS['COLD'])

    rel_residuals = np.abs(model_result['detflat'].data - detflat_model.data) / model_result['detflat'].err
    assert np.sum(rel_residuals > 5) == 0

    # Check 1 sigma statistics of the flat field residuals
    confidence_level = np.sum(rel_residuals < 1) / np.size(rel_residuals)
    assert abs(confidence_level-0.683) < 0.1