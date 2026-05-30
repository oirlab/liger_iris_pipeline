from liger_iris_pipeline import datamodels
from liger_iris_pipeline import DarkSubtractionStep, RegisterCalibrationStep
from liger_iris_pipeline.calibrations import LigerCalibrationStore, DarkSelector
from koa_middleware.utils import generate_md5_file

import astropy.time
import numpy as np
import os

def test_local_caldb(tmp_path, datadir):

    # Calibration cache
    os.environ['KOA_CALIBRATION_CACHE'] = str(tmp_path) + '/KOA_CALIBRATION_CACHE/'

    # Store 5 files in the local cache
    N = 5
    dark_models = []
    mjds = astropy.time.Time.now().mjd + np.arange(N) * 365
    for i in range(N):
        dark_model = datamodels.DarkModel(meta={'exposure.mjd_start': mjds[i], 'instrument.mode': 'IMG'})
        step = RegisterCalibrationStep()
        step.run(dark_model)
        dark_models.append(dark_model)

    # Connect to DB
    with LigerCalibrationStore(connect_remote=False) as store:

        # Test if the local files are registered
        results = store.query()
        assert len(results) == N, f"Expected {N} files in the local DB, but found {len(results)}"

        # Ensure we select the first dark
        mjd0 = astropy.time.Time.now().mjd + 1
        input_model = datamodels.ImagerModel(meta={'exposure.mjd_start': mjd0, 'instrument.mode': 'IMG', 'instrument.name': 'Liger'})
        dark1_filepath, _ = store.select_and_get_calibration(
            input_model.meta,
            DarkSelector()
        )
        assert dark1_filepath == dark_models[0]._filepath, "Wrong dark model retrieved from local DB"

        # Test retrieval of second dark
        input_model = datamodels.ImagerModel(meta={'exposure.mjd_start': mjd0 + 365, 'instrument.mode': 'IMG', 'instrument.name': 'Liger', 'data_level' : '1'})
        dark2_filepath, _ = store.select_and_get_calibration(
            input_model.meta,
            DarkSelector()
        )
        assert dark2_filepath == dark_models[1]._filepath, "Wrong dark model retrieved from local DB"

        # Test retrieval of third dark
        input_model = datamodels.ImagerModel(meta={'exposure.mjd_start': mjd0 + 2 * 365, 'instrument.mode': 'IMG', 'instrument.name': 'Liger', 'data_level' : '1'})
        dark3_filepath, _ = store.select_and_get_calibration(
            input_model.meta,
            DarkSelector()
        )
        assert dark3_filepath == dark_models[2]._filepath, "Wrong dark model retrieved from local DB"
        # Test retrieval from DarkSubtractionStep
        dark_step = DarkSubtractionStep()
        dark4_filepath, _ = dark_step.get_calibration(input_model, 'dark')
        assert dark4_filepath == dark_models[2]._filepath, "Wrong dark model retrieved via DarkSubtractionStep"

        # Check calibration retrieval by ID
        for dark_model in dark_models:
            dark_record = store.query(cal_id=dark_model.meta.cal_id)
            assert dark_record['id'] == dark_model.meta.cal_id, "Calibration ID mismatch"

        # Check MD5 checksum in two ways
        for dark_model in dark_models:
            dark_record = store.query(cal_id=dark_model.meta.cal_id)
            file_md5_from_record = dark_record['file_md5']
            assert file_md5_from_record is not None, "MD5 checksum is None in the DB record"
            assert file_md5_from_record == generate_md5_file(dark_model._filepath), "MD5 checksum mismatch between record and live file"


def test_sync_db_from_existing_files(tmp_path, datadir):

    # Calibration cache
    os.environ['KOA_CALIBRATION_CACHE'] = str(tmp_path) + '/KOA_CALIBRATION_CACHE/'

    # Store 5 files in the local cache without registering them.
    N = 5
    dark_models = []
    mjds = astropy.time.Time.now().mjd + np.arange(N) * 365
    for i in range(N):
        dark_model = datamodels.DarkModel(meta={'exposure.mjd_start': mjds[i], 'origin' : 'KECK', 'instrument.mode': 'IMG', 'instrument.name': 'Liger'})
        dark_models.append(dark_model)

    # Init the store to create the directores and local DB.
    # The local DB file will be created, but this is irrelevant
    with LigerCalibrationStore(connect_remote=False) as store:

        # Save to cache dir manually without registering in DB
        for dark_model in dark_models:
            dark_model.save(
                output_dir=store.data_dir
            )

    # Connect to DB
    with LigerCalibrationStore(connect_remote=False) as store:

        # Ensure the local DB is empty
        results = store.query()
        assert len(results) == 0, f"Expected 0 files in the local DB, but found {len(results)}"

        # Sync from local files
        cals_added = store.sync_records_from_cached_files()

        # Test if the local files are registered
        results = store.query()
        assert len(results) == N, f"Expected {N} files in the local DB, but found {len(results)}"


def test_calibration_versioning_with_datamodels(tmp_path):
    N = 3
    dark_models = []

    os.environ['KOA_CALIBRATION_CACHE'] = str(tmp_path) + '/KOA_CALIBRATION_CACHE/'

    mjd = astropy.time.Time.now().mjd

    for i in range(N):
        dark_model = datamodels.DarkModel(
            meta={
                'exposure.mjd_start': mjd,
                'master_cal': True,
                'instrument.mode': 'IMG',
                'instrument.ifs_mode': 'N/A',
                'instrument.name': 'Liger'
            }
        )
        dark_models.append(dark_model)

    with LigerCalibrationStore(connect_remote=False) as store:

        for idx, dark_model in enumerate(dark_models):
            version = store._get_next_calibration_version(dark_model, origin='LOCAL')
            expected_version = f"{idx+1:03d}"
            assert version == expected_version
            _, _ = store.register_calibration(dark_model, origin='LOCAL', new_version=True)

        # Change datetime_obs via mjd_start → new family
        new_dark = datamodels.DarkModel(
            meta={
                'exposure.mjd_start': mjd + 1,
                'master_cal': True,
                'instrument.mode': 'IMG',
                'instrument.ifs_mode': 'N/A',
                'instrument.name': 'Liger'
            }
        )

        next_version = store._get_next_calibration_version(new_dark, origin='LOCAL')
        assert next_version == "001"

        # Change master_cal → new family
        new_dark = datamodels.DarkModel(
            meta={
                'exposure.mjd_start': mjd,
                'master_cal': False,
                'instrument.mode': 'IMG',
                'instrument.ifs_mode': 'N/A',
                'instrument.name': 'Liger'
            }
        )

        next_version = store._get_next_calibration_version(new_dark, origin='LOCAL')
        assert next_version == "001"

        # Change instrument mode -> new family
        new_dark = datamodels.DarkModel(
            meta={
                'exposure.mjd_start': mjd,
                'master_cal': True,
                'instrument.mode': 'IFS',
                'instrument.ifs_mode': 'LENSLET',
                'instrument.name': 'Liger'
            }
        )

        next_version = store._get_next_calibration_version(new_dark, origin='LOCAL')
        assert next_version == "001"