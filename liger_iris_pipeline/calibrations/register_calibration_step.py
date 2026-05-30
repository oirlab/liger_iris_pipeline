from ..stpipe.base_step import LigerIRISStep
from .. import datamodels

import os

__all__ = ['RegisterCalibrationStep']


class RegisterCalibrationStep(LigerIRISStep):
    """
    Registers a reference file model in the local calibration database.

    Parameters
    ----------
    input : CalibrationModel
        The model to be registered in the local database.
    origin : str, optional
        The origin to register the calibration under. Default is 'local'.

    Returns
    -------
    output : CalibrationModel
        The calibration model that was registered.
    """

    spec = """
        origin = string(default='LOCAL')  # Origin to register the calibration under
    """

    class_alias = "register_cal"

    def process(self, input):
        cal_model = datamodels.open(input)

        assert isinstance(
            cal_model, datamodels.CalibrationModel
        ), f"Input model must be a valid CalibrationModel, got {type(cal_model)}"

        from . import LigerCalibrationStore
        
        with LigerCalibrationStore(
            connect_remote=False
        ) as store:
            
            local_filepath, cal_record = store.register_calibration(
                cal_model, origin=self.origin
            )

        return dict(
            output=cal_model,
            cal_record=cal_record,
            local_filepath=local_filepath
        )