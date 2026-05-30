import numpy as np

from liger_iris_pipeline.refpix import RefPixelCorrectionStep
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.datamodels import DQ_FLAGS
from liger_iris_sim.utr.create_ramp import create_ramp

def test_stage1_refpix_step(tmp_path):
    np.random.seed(12345)

    # --- Define parameters for the simulated ramp ---
    max_cores = 1
    max_slope = 0  # e-/s
    readtime = 1.7  # seconds
    n_reads = 2
    # ny, nx = 100, 100 # size of the detector
    ny, nx = 2048, 2048 # size of the detector
    # ny, nx = 4096, 4096 # size of the detector
    n_channels = 4  # number of readout channels

    meta = {'instrument.name' : 'Liger', 'instrument.mode': 'IMG', 'instrument.n_channels': n_channels}

    # --- Non-linearity and its inverse polynomial coefficients ---

    # Create an ideal ramp (1D array for demonstration)
    ideal_ramp = np.linspace(0, 1.5*np.iinfo(np.uint16).max, 1001, endpoint=True)
    # nonlin_coeffs = [-1e-6, 1, 0]  # Example coefficients for a cubic non-linearity
    nonlin_coeffs = [ 1, 0]  # Example coefficients for a cubic non-linearity
    nonlinear_ramp = np.polyval(nonlin_coeffs, ideal_ramp)

    # Fit inverse polynomial (correction) coefficients
    nonlin_correction_coefs = np.polyfit(nonlinear_ramp, ideal_ramp, deg=5)

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
    dqinit_map[5, :] |= DQ_FLAGS["DO_NOT_USE"]
    dqinit_model = datamodels.DQModel(dq=dqinit_map, meta=meta)

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
    kTC_noise = 0  # e-/s
    kTC_noise_map = np.full((ny, nx), kTC_noise, dtype=np.float32)
    bias_model = datamodels.BiasModel(
        data=bias_map / gain_map,  # bias in DN/s
        ktc=kTC_noise_map / gain_map,  # kTC in DN/s
        meta=meta,
    )

    # --- Create random flat map ---
    detflat_map = np.random.normal(loc=1, scale=0.1, size=(ny, nx)).astype(np.float32)
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
        rn_err=np.zeros_like(rn_map),
        meta=meta,
    )


    # --- Create a fake UTR cube ---
    electron_rate_map = np.linspace(0, max_slope, nx, dtype=np.float32)[None, :] * np.ones((ny, 1), dtype=np.float32)
    ramp_data = create_ramp(
        electron_rate_map,  # in e-/s
        readtime=readtime, n_reads=n_reads,
        nonlin_coeffs=nonlin_coeffs,
        gain=gain_map,  # in e-/s
        flat=detflat_map,
        dark=dark_map,  # in e-/s
        bias=bias_map,  # in e-/s
        kTC_noise=0,  # in e-/s
        poisson_noise=False, read_noise=None,  # in e-
        convert_to_uint16=False, clip_ramps=True,
        max_cores=max_cores,
        std_1overf=RN*10/gain, # DN
        n_channels = n_channels,
        vertical=True
    )

    #adding a jump
    # ramp_data['data'][4::,:,0:nx//2] += 1000

    ramp_model = datamodels.RampModel(
        data=ramp_data['data'],
        dq_raw=ramp_data['dq_raw'],
        meta=ramp_data['meta']
    )
    
    ramp_model.meta.filename = "simulated_ramp.fits"

    step_args = {
        'method' : 'scales_drp',
        'n_channels' : n_channels,
        'n_ref_left' : 4,
        'n_ref_right' : 4
    }
    refpix_step = RefPixelCorrectionStep(**step_args)
    model_result = refpix_step.run(ramp_model.copy())

    for i in range(n_reads):
        assert np.nanstd(model_result.data[i, :, :]) < 0.9 * np.nanstd(ramp_model.data[i, :, :])