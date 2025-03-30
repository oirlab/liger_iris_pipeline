# Imports
import liger_iris_pipeline
import numpy as np
from liger_iris_pipeline.tests.utils import create_ramp

def create_config():
    conf = """
    class = "liger_iris_pipeline.Stage1Pipeline"
    save_results = True

    [steps]
        [[nonlinear_correction]]
            skip = False
        [[ramp_fit]]
            method = "ols"
    """
    return conf

def test_imager_stage1(tmp_path):

    meta = {
        'model_type' : 'RampModel',
        'target.name': 'Uniform',
        'target.ra' : 0.0,
        'target.dec' : 0.0,
        'target.airmass_start' : 1.0,
        'exposure.itime' : 90,
        'exposure.nframes' : 1,
        'exposure.jd_start' : 2460577.5,
        'exposure.type' : 'SCI',
        'instrument.name' : 'IRIS',
        'instrument.detector' : 'IMG1',
        'instrument.grating' : 'None',
        'instrument.mode' : 'IMG',
        'instrument.ifumode' : 'None',
        'instrument.filter' : 'Y',
        'instrument.scale' : 0.004,
    }

    # Uniform photon rate
    source = np.full((10, 10), 1000.0, dtype=np.float32)
    
    # Create a ramp model
    ramp_model = create_ramp(source, meta, readtime=1, n_reads_per_group=10, n_groups=5, nonlin_coeffs = None, noise=False)
    ramp_filename = str(tmp_path / "2024B-P123-008_IRIS_IMG1_SCI-Y_LVL0_0001-00.fits")
    ramp_model.save(ramp_filename)

    # Create a temporary config file
    conf = create_config()
    config_file = str(tmp_path / "test_config.cfg")
    with open(config_file, "w") as f:
        f.write(conf)

    # Create the pipeline
    pipeline = liger_iris_pipeline.Stage1Pipeline(config_file=config_file, output_dir=str(tmp_path))

    # Test UTR
    pipeline.ramp_fit.method = "ols"
    results = pipeline.run(ramp_filename)
    model_result = results[0]
    np.testing.assert_allclose(model_result.data, source, rtol=1e-6)
    
    # Test MCDS
    pipeline.ramp_fit.method = "mcds"
    pipeline.ramp_fit.num_coadd = 3
    results = pipeline.run(ramp_filename)
    model_result = results[0]
    np.testing.assert_allclose(model_result.data, source, rtol=1e-6)

    # Test CDS
    pipeline.ramp_fit.method = "mcds"
    pipeline.ramp_fit.num_coadd = 1
    results = pipeline.run(ramp_filename)
    model_result = results[0]
    np.testing.assert_allclose(model_result.data, source, rtol=1e-6)