from liger_iris_pipeline.pipeline import ProcessBiasPipeline
from liger_iris_pipeline import datamodels
from liger_iris_sim.utr.create_ramp import create_ramp
import numpy as np

def test_stage1_bias_calib(tmp_path):
    np.random.seed(1)

    # Ramp Parameters
    max_slope = 200  # e-/s
    readtime = 1.7   # seconds
    n_reads = 1      # Total number of reads per UTR file
    n_frames = 100   # number of simulated UTR files to create
    ny, nx = 10, 10  # size of the detector

    #### CREATE DUMMY DETECTOR CALIBRATIONS ####

    # Nonlinear coeffs (perfectly linear)
    nonlin_coeffs = [1, 0]

    # DQ Map
    dq_map = np.zeros((ny, nx), dtype=np.uint32)
    dqinit_model = datamodels.DQModel(dq=dq_map)
    
    # Gain
    gain = 2  # e-/DN
    gain_map = np.full((ny, nx), gain, dtype=np.float32)
    
    # Dark current
    dark_current = 0.0025  # e-/s
    dark_map = np.random.normal(
        loc=dark_current,
        scale=dark_current / 10,
        size=(ny, nx)
    ).astype(np.float32)
    
    # Bias
    bias = 1000  # e-
    kTC_noise = 50  # e- RMS
    bias_map = np.full((ny, nx), bias, dtype=np.float32)
    kTC_noise_map = np.full((ny, nx), kTC_noise, dtype=np.float32)
    
    # Detector flat
    detflat_map = np.ones((ny, nx), dtype=np.float32)

    RN = 8.0  # e- RMS
    rn_map = np.full((ny, nx), RN, dtype=np.float32)

    #### Create UTR Cubes ####
    electron_rate_map = np.full((ny, nx), max_slope, dtype=np.float32)
    ramp_model_sequence = []
    for k in range(n_frames):
        ramp_data = create_ramp(
            electron_rate_map,  # in e-/s
            readtime=readtime, n_reads=n_reads,
            nonlin_coeffs=nonlin_coeffs,
            gain=gain_map,  # in e-/DN
            flat=detflat_map,
            dark=dark_map,  # in e-/s
            bias=bias_map,  # in e-/s
            kTC_noise=kTC_noise,  # in e-/s
            poisson_noise=True, read_noise=rn_map,  # in e-/s
            convert_to_uint16=True, clip_ramps=True,
            max_cores=1
        )

        ramp_model = datamodels.RampModel(
            data=ramp_data['data'], dq_raw=ramp_data['dq_raw'],
            meta=ramp_data['meta']
        )
        ramp_model.meta.filename = f"simulated_ramp{k}.fits"

        ramp_model_sequence.append(ramp_model)

    # Step params
    steps = {
        'dq_init': {
            'dq': dqinit_model
        },
    }

    # Setup and call the stage 0 pipeline
    bias_pipe = ProcessBiasPipeline(steps=steps)

    # Run pipeline
    model_result = bias_pipe.run(ramp_model_sequence)
    
    # Test (Bias - true Bias)
    residuals_bias = np.abs(model_result.data - bias_map / gain_map)
    assert np.sum(residuals_bias > 20) == 0 # NOTE: 20 depends on sim params 

    # Test (kTC - true kTC)
    residuals_kTC = np.abs(model_result.err - kTC_noise_map / gain_map) # in DN
    assert np.sum(residuals_kTC > 10) == 0 # NOTE: 10 depends on sim params