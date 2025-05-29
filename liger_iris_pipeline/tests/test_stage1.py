# Imports
import liger_iris_pipeline
import numpy as np
from liger_iris_pipeline.tests.utils import create_ramp, get_meta, download_osf_file

def test_imager_stage1(tmp_path):

    # Get nonlin corr file
    nonlincoeff_path = download_osf_file('Liger/Cals/Liger_IMG_NONLINCOEFF_20240924000000_0.0.1.fits', use_cached=True)

    # Create a ramp model
    source = np.full((10, 10), 1000.0, dtype=np.float32)
    ramp_model = create_ramp(source, readtime=1.0, n_reads_per_group=10, n_groups=5, read_noise=0, nonlin_coeffs=None, poisson_noise=False)
    ramp_model.meta.instrument.name = 'Liger'
    ramp_model.meta.instrument.mode = 'IMG'
    get_meta(ramp_model)

    # Create the pipeline
    pipeline = liger_iris_pipeline.Stage1Pipeline()

    # Test UTR
    pipeline.ramp_fit.method = "ols"
    pipeline.nonlinear_correction.nonlincoeff = nonlincoeff_path
    model_result = pipeline.run(ramp_model)
    np.testing.assert_allclose(model_result.data, source, rtol=1e-6)
    
    # Test MCDS
    pipeline.ramp_fit.method = "mcds"
    pipeline.ramp_fit.num_coadd = 3
    model_result = pipeline.run(ramp_model)
    np.testing.assert_allclose(model_result.data, source, rtol=1e-6)

    # Test CDS
    pipeline.ramp_fit.method = "cds"
    pipeline.ramp_fit.num_coadd = 1 # Redundant but explicit
    model_result = pipeline.run(ramp_model)
    np.testing.assert_allclose(model_result.data, source, rtol=1e-6)