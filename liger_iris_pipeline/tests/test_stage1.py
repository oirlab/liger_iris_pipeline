# Imports
import liger_iris_pipeline
from liger_iris_pipeline.associations import IRISImagerL0Association
import numpy as np
from liger_iris_pipeline.tests.test_utils import create_ramp

def create_config():
    conf = """
    name = "ImagerStage0Pipeline"
    class = "liger_iris_pipeline.pipeline.ImagerStage0Pipeline"
    save_results = True

    [steps]
        [[nonlinear_correction]]
            skip = False
        [[ramp_fit]]
            method = "mcds"
    """
    return conf

def test_imager_stage1(tmp_path):

    # Create a temporary ASN file
    asn = create_asn()
    #asn.add(["members"][0]["expname"] = str(tmp_path / asn["products"][0]["members"][0]["expname"])

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
    source = np.full((10, 10), 1000)
    
    # Create a ramp model
    ramp_model = create_ramp(source, meta, readtime=1, n_reads_per_group=10, n_groups=5, nonlin_coeffs = None)
    
    # Save the ramp model
    ramp_model.save(asn["products"][0]["members"][0]["expname"])

    # Save ASN
    asn_file = tmp_path / "test_asn.json"
    asn.dump(asn_file)

    # Create a temporary config file
    conf = create_config()
    config_file = tmp_path / "test_config.cfg"
    with open(config_file, "w") as f:
        f.write(conf)

    # Create and call the pipeline object
    # Pipeline saves L2 file: 2024A-P123-044_IRIS_IMG1_SCI-J1458+1013-SIM-Y_LVL2_0001.fits
    results, _ = liger_iris_pipeline.Stage1Pipeline.call(asn_file, config_file=config_file, return_step=True)
    model_result = results[0]

    # Test MCDS
    np.testing.assert_allclose(model_result.data, source, rtol=1e-6)

    # Test UTR
    conf = conf.replace('mcds', 'utr')
    with open(config_file, "w") as f:
        f.write(conf)
    
    results, _ = liger_iris_pipeline.Stage1Pipeline.call(asn_file, config_file=config_file, return_step=True)
    model_result = results[0]

    # Test UTR
    np.testing.assert_allclose(model_result.data, source, rtol=1e-6)