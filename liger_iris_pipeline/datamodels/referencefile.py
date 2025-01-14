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


    def __init__(self, init=None, **kwargs):
        super().__init__(init=init, **kwargs)
        self._no_asdf_extension = True


    def save(self, path, dir_path=None, *args, **kwargs):
        """
        Save data model.  If the 'dq' and 'dq_def' exist they need special
        handling.
        """
        if (self.hasattr('dq_def') and self.hasattr("dq")
           and self.dq is not None and self.dq_def is not None):
            # Save off uncompressed DQ array.  Compress DQ array
            # according to 'dq_def' for save.  Then restore
            # uncompressed DQ array.
            dq_orig = self.dq.copy()
            self.dq = dynamic_mask(self, pixel, inv=True)
            output_path = super().save(path, dir_path, *args, **kwargs)
            self.dq = dq_orig
        else:
            output_path = super().save(path, dir_path, *args, **kwargs)
        return output_path


    def print_err(self, message):
        if self._strict_validation:
            raise ValueError(message)
        else:
            warnings.warn(message, ValidationWarning)


    @staticmethod
    def _generate_filename(
        instrument : str,
        detector : str, reftype : str,
        date : str, version : str
    ):
        """IRIS_IMG1_FLAT_20240101T000000_0.0.1.fits"""
        # TODO: Automate versioning
        if instrument.lower() == 'iris':
            instrument = 'IRIS'
        elif instrument.lower() == 'liger':
            instrument = 'Liger'
        else:
            raise ValueError(f"Unknown instrument {instrument}")
        return f"{instrument}_{detector.upper()}_{reftype}_{date}_{version}.fits"
    
    def generate_filename(
            self,
            instrument : str | None = None,
            detector : str | None = None,
            reftype : str | None = None,
            date : str | None = None,
            version : str | None = None
        ):
        instrument = instrument if instrument is not None else self.instrument
        detector = detector if detector is not None else self.meta.instrument.detector
        reftype = reftype if reftype is not None else self.meta.reftype
        date = self.meta.date.replace(':', '').replace('-', '')[0:15]
        version = self.meta.ref_version if self.meta.ref_version is not None else '0.0.1'
        return self._generate_filename(
            instrument=instrument, detector=detector, reftype=reftype,
            date=date, version=version
        )