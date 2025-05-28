import warnings

from stdatamodels.validate import ValidationWarning
from stdatamodels.dynamicdq import dynamic_mask

from .model_base import LigerIRISDataModel
from .dqflags import pixel


__all__ = ['ReferenceFileModel']


class ReferenceFileModel(LigerIRISDataModel):
    """
    A base data model for Liger and IRIS calibration reference data.
    """
    schema_url = "https://oirlab.github.io/schemas/ReferenceFileModel.schema"
    _ref_type = None


    # def __init__(self, init=None, **kwargs):
    #     super().__init__(init=init, **kwargs)
    #     self._no_asdf_extension = True

    def on_init(self, *args, **kwargs):
        super().on_init(*args, **kwargs)
        self.meta.ref_type = self._ref_type


    def print_err(self, message):
        if self._strict_validation:
            raise ValueError(message)
        else:
            warnings.warn(message, ValidationWarning)


    @staticmethod
    def _generate_filename(
        instrument : str, detector : str, ref_type : str, date_time : str,
        version : str | None = None, suffix : str | None = None
    ):
        # TODO: Automate versioning
        if version is None:
            version = '0.0.1'
        if instrument.lower() == 'iris':
            instrument = 'IRIS'
        elif instrument.lower() == 'liger':
            instrument = 'Liger'
        else:
            raise ValueError(f"Unknown instrument {instrument}")
        if suffix is None:
            suffix = ''
        else:
            suffix = '_' + suffix
        return f"{instrument}_{detector.upper()}_{ref_type.upper()}_{date_time}_{version}{suffix}.fits"
    
    
    def generate_filename(self, suffix : str | None = None):
        return self._generate_filename(
            instrument=self.meta.instrument.name, detector=self.meta.instrument.detector, ref_type=self._ref_type,
            date_time=self.meta.exposure.datetime_start, version=self.meta.ref_version, suffix=suffix
        )