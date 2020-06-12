import os
import iris_pipeline
iris_pipeline.monkeypatch_jwst_datamodels()

def test_rop1():
    iris_pipeline.pipeline.ROPPipeline.call('data/sample_ramp_new.fits', config_file="data/drsrop.cfg")
    return 1


