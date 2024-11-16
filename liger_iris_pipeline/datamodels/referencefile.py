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
    schema_url = "https://oirlab.github.io/schemas/LigerReferenceFileModel.schema"


    def __init__(self, init=None, **kwargs):
        super().__init__(init=init, **kwargs)
        self._no_asdf_extension = True
        self.meta.telescope = "keck"


    def validate(self):
        """
        Convenience function to be run when files are created.
        Checks that required reference file keywords are set.
        """
        to_fix = []
        to_check = ['description', 'reftype', 'author', 'pedigree', 'useafter']
        for field in to_check:
            if getattr(self.meta, field) is None:
                to_fix.append(field)
        if self.meta.instrument.name is None:
            to_fix.append('instrument.name')
        if self.meta.telescope != 'keck':
            to_fix.append('telescope')
        if to_fix:
            self.print_err(f'Model.meta is missing values for {to_fix}')
        super().validate()


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