
import numpy as np
import liger_iris_pipeline
from liger_iris_pipeline.distortion import DistortionCorrectionStep
from liger_iris_pipeline import datamodels
from liger_iris_pipeline.utils.gdrive import download_gdrive_file

import matplotlib.pyplot as plt

def test_distortion_step(tmp_path=None):
    #sci_L1_filepath = download_gdrive_file('Liger/L1/2024B-P001-001_Liger_IMG_SCI_LVL1_0001_M13-J-10mas.fits', use_cached=True)
    #distortion_filepath = download_gdrive_file('Liger/Cals/Liger_IMG_DARK_20240924000000_0.0.1.fits', use_cached=True)

    #sci_L1_filepath = '/Users/cale/Desktop/Liger_IRIS_Test_Data/Liger/L1/2024B-P001-001_Liger_IMG_SCI1_0001_M13-J-10mas-skyscale1.0.fits'

    data = np.ones((2048, 2048), dtype=np.float32)
    sci_model = datamodels.ImagerModel(
            data=data,
            err=np.ones_like(data),
            var_poisson=np.ones_like(data),
            var_rnoise=np.ones_like(data),
            meta={
                'instrument.mode' : 'IMG',
                'instrument.filter': 'J',
                'exposure.exposure_time': 60.0,
                'exposure.nframes': 1,
            }
        )

    distortion_filepath = '/Users/cale/Desktop/Liger_IRIS_Test_Data/Liger/Cals/Liger_IMG_DISTORTION_MAP_20240924000000.fits'
    step_output = DistortionCorrectionStep.call(sci_model, distortion=distortion_filepath)