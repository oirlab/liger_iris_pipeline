import os
import liger_iris_pipeline
from liger_iris_pipeline.tests.test_utils import get_data_from_url
liger_iris_pipeline.monkeypatch_jwst_datamodels()
import numpy as np


def setup_inputs(
    ngroups=4,
    readnoise=10,
    nints=1,
    nrows=40,
    ncols=40,
    nframes=1,
    grouptime=1.0,
    gain=1,
    deltatime=1,
):
    arr = np.array(
        [
            np.zeros([40, 40]),
            np.ones([40, 40]) * 4000,
            np.ones([40, 40]) * 8000,
            np.ones([40, 40]) * 12000,
        ],
        dtype=np.float64,
    )
    arr = np.array([arr])
    times = np.array(list(range(ngroups)), dtype=np.float64) * deltatime
    gain = np.ones(shape=(nrows, ncols), dtype=np.float64) * gain
    err = np.ones(shape=(nints, ngroups, nrows, ncols), dtype=np.float64)
    data = np.zeros(shape=(nints, ngroups, nrows, ncols), dtype=np.float64)
    data = arr
    pixdq = np.zeros(shape=(nrows, ncols), dtype=np.float64)
    gdq = np.zeros(shape=(nints, ngroups, nrows, ncols), dtype=np.int32)
    model_ramp = liger_iris_pipeline.datamodels.RampModel(
        data=data, err=err, pixeldq=pixdq, groupdq=gdq, times=times
    )
    model_ramp.meta.telescope = "TMT"
    model_ramp.meta.observation.time = "00:00:00"
    model_ramp.meta.observation.date = "2020-07-13"
    model_ramp.meta.instrument.name = "IRIS"
    model_ramp.meta.instrument.detector = "IRIS1"
    model_ramp.meta.instrument.filter = "K"
    model_ramp.meta.observation.date = "2015-10-13"
    model_ramp.meta.exposure.type = "IRIS_IMAGE"
    model_ramp.meta.exposure.group_time = deltatime
    model_ramp.meta.subarray.name = "CUSTOM"
    model_ramp.meta.subarray.xstart = 1
    model_ramp.meta.subarray.ystart = 1
    model_ramp.meta.subarray.xsize = 40
    model_ramp.meta.subarray.ysize = 40
    model_ramp.meta.exposure.frame_time = deltatime
    model_ramp.meta.exposure.ngroups = ngroups
    model_ramp.meta.exposure.group_time = deltatime
    model_ramp.meta.exposure.nframes = 1
    model_ramp.meta.exposure.groupgap = 0
    model_ramp.times = times
    return model_ramp


def test_rop1():
    raw_readout_filename = get_data_from_url("48191977")
    liger_iris_pipeline.pipeline.ROPPipeline.call(
        raw_readout_filename, config_file="liger_iris_pipeline/tests/data/drsrop.cfg"
    )
    return 1


def test_rop2():
    model_ramp = setup_inputs()
    image_model = liger_iris_pipeline.pipeline.ROPPipeline.call(
        model_ramp, config_file="liger_iris_pipeline/tests/data/drsrop.cfg"
    )
    assert np.mean(image_model.data) == 8048.5
