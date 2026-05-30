from typing import ClassVar
from liger_iris_drp_resources import load_filters_summary
from .meta_utils import get_semester_id

__all__ = ['IRISConfig']

clock_rate = 150_000

class IRISConfig:

    instrument_name : ClassVar[str] = 'IRIS'
    telescope_name : ClassVar[str] = 'TMT'
    clock_rate : ClassVar[float] = clock_rate
    
    @classmethod
    def set_defaults(cls, model):

        # Telescope
        model.meta.telescope = cls.telescope_name

        # Pixel scale
        if model.meta.instrument.scale is None:
            if model.meta.instrument.mode == 'IMG':
                model.meta.instrument.scale = 0.004

        # Detector
        if model.meta.instrument.detector in (None, 'N/A', 'None'):
            if model.meta.instrument.mode == 'IMG':
                model.meta.instrument.detector = 'IMG1'
            elif model.meta.instrument.mode in ('LENSLET', 'SLICER'):
                model.meta.instrument.detector = 'IFS'
            
        # Filter wavelengths
        if model.meta.instrument.filter not in (None, 'N/A', 'None'):
            filter_info = load_filters_summary(model.meta.instrument.filter)
            model.meta.instrument.wave_min = filter_info['wavemin']
            model.meta.instrument.wave_center = filter_info['wavecenter']
            model.meta.instrument.wave_max = filter_info['wavemax']

        # Program ID and semester
        if model.meta.program.program_id is None:
            model.meta.program.program_id = 'P001'
        if model.meta.program.semester_id is None:
            model.meta.program.semester_id = get_semester_id(model.meta.datetime_obs)

        # Exposure type
        if model.meta.exposure.type is None:
            model.meta.exposure.type = 'SCI'