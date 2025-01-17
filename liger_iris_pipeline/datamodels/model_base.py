import os
from pathlib import Path

from astropy.time import Time
from astropy.io import fits
from datetime import datetime
from stdatamodels import DataModel

__all__ = ["LigerIRISDataModel"]

class LigerIRISDataModel(DataModel):
    """
    The base data model for Liger and IRIS.
    This class should not be instantiated on its own.
    """
    schema_url = "https://oirlab.github.io/schemas/LigerIRISDataModel.schema"

    def __init__(self, init=None, instrument : str | None = None, **kwargs):
        
        # Pass to super if already a datamodel, schema already known
        if isinstance(init, LigerIRISDataModel):
            self.set_schema_from_instrument(instrument=init.instrument)
            super().__init__(init=init, **kwargs)
        else:
            # Get the schema from instrument name
            if instrument is not None:
                self.set_schema_from_instrument(instrument)
            elif isinstance(init, str | Path):
                self.set_schema_from_fits_filename(init)
            elif isinstance(init, fits.HDUList):
                self.set_schema_from_hdulist(init)
            # TODO: FIX CASE WHEN NO INSTRUMENT IS PROVIDED. CRDS REQUIRES THIS.
            #else:
                #raise ValueError(f"Cannot determine schema from {init}")
            
            # Call super with schema_url now set
            super().__init__(init=init, **kwargs)

        if isinstance(init, str | Path):
            self._filename = str(init)
        elif isinstance(init, fits.HDUList):
            self._filename = init.filename()
        else:
            self._filename = None

    def set_schema_from_instrument(self, instrument : str):
        s = self.schema_url.rsplit('/', 1)
        self.schema_url = s[0] + '/' + instrument + s[-1]

    # Silly to open file twice but oh well for now
    def set_schema_from_fits_filename(self, init : str | Path):
        init = str(init)
        if not os.path.exists(init):
            raise ValueError(f"Path {init} does not exist")
        
        try:
            instrument = fits.getval(init, keyword='INSTRUME', ext=0)
            self.set_schema_from_instrument(instrument)
        except KeyError:
            raise KeyError(f"Keyword 'INSTRUME' not found in file {init}")
        
    def set_schema_from_hdulist(self, init : fits.HDUList):
        try:
            instrument = init[0].header['INSTRUME']
            self.set_schema_from_instrument(instrument)
        except KeyError:
            raise KeyError(f"Keyword 'INSTRUME' not found in file {init}")
        
    def __setattr__(self, attr, value):
        if attr == 'schema_url':
            self.__dict__[attr] = value
        else:
            super().__setattr__(attr, value)
    

    def get_crds_parameters(self):
        """
        Get parameters used by CRDS to select references for this model.

        Returns:
        dict : the CRDS parameters
        """
        return {
            key: val
            for key, val in self.to_flat_dict(include_arrays=False).items()
            if isinstance(val, (str, int, float, complex, bool))
        }

    def on_init(self, init):
        """
        Hook invoked by the base class before returning a newly
        created model instance.
        """
        super().on_init(init)

        if not self.meta.hasattr("date"):
            self.meta.date = Time.now().isot

    def on_save(self, init):
        """
        Hook invoked by the base class before writing a model
        to a file (FITS or ASDF).
        """
        super().on_save(init)
        if self.meta.filename is None and isinstance(init, str | Path):
            self.meta.filename = str(os.path.basename(init))
        elif isinstance(init, str | Path):
            if self.meta.filename != str(init):
                self.meta.filename = str(init)
        self.meta.date_created = Time.now().isot

    @property
    def input_path(self):
        if self.filename is not None:
            return os.path.split(os.path.abspath(self.filename))[0]
        else:
            return None
        
    @property
    def crds_observatory(self):
        return "ligeriri"

    @property
    def telescope(self):
        return self.meta.telescope
    
    @property
    def instrument(self):
        return self.meta.instrument.name
    
    @staticmethod
    def _generate_filename(
        instrument : str,
        sem_id : str | None,
        program_number : str | None, obs_number : str | None,
        detector : str, exptype : str, level : int | str = 0,
        exp : int | str = '0001', subarray : int | str | None = None
    ):
        if sem_id is None:
            t = datetime.now()
            sem_id = str(t.year)
            if t.month < 8:
                sem_id += 'A'
            else:
                sem_id += 'B'
        if program_number is None:
           program_number = 'P001' 
        if obs_number is None:
            obs_number = '001'
        if instrument.lower() == 'iris':
            instrument = 'IRIS'
        elif instrument.lower() == 'liger':
            instrument = 'Liger'
        else:
            raise ValueError(f"Unknown instrument {instrument}")
        if isinstance(exp, int):
            exp = str(exp).zfill(4)
        if type(subarray) in (int, str):
            subarray = '-' + str(subarray).zfill(2)
        else:
            subarray = '-00'
        return f"{sem_id}-{program_number}-{obs_number}_{instrument}_{detector.upper()}_{exptype}_LVL{int(level)}_{exp}{subarray}.fits"
    
    def generate_filename(
            self,
            instrument : str | None = None,
            sem_id : str | None = None,
            program_number : str | None = None, obs_number : str | None = None,
            detector : str | None = None, exptype : str | None = None, level : int | str | None = None,
            exp : int | str | None = None, subarray : int | str | None = None
        ):
        instrument = instrument if instrument is not None else self.instrument
        sem_id = sem_id if sem_id is not None else self.meta.program.sem_id
        program_number = program_number if program_number is not None else self.meta.program.program_number
        obs_number = obs_number if obs_number is not None else self.meta.program.obs_number
        detector = detector if detector is not None else self.meta.instrument.detector
        exptype = exptype if exptype is not None else self.meta.exposure.type
        level = level if level is not None else self.meta.data_level
        exp = exp if exp is not None else self.meta.exposure.number
        subarray = subarray if subarray is not None else self.meta.subarray.id

        # Override exptype for now to include additional info for development
        # NOTE: Remove this eventually
        exptype += f'-{self.meta.target.name}' + f'-{self.meta.instrument.filter}' + f'-{self.meta.instrument.scale}'

        return self._generate_filename(
            instrument=instrument,
            sem_id=sem_id, program_number=program_number, obs_number=obs_number,
            detector=detector, exptype=exptype,
            level=level, exp=exp, subarray=subarray
        )

    def get_primary_array_name(self):
        return 'data'
    
    # @classmethod
    # def from_model(cls, input_model):
    #     model = cls(instrument=input_model.instrument)
    #     model.__dict__.update(input_model.__dict__)
    #     return model
    
    def copy(self, memo=None):
        """
        Returns a deep copy of this model.
        """
        result = self.__class__(instrument=self.instrument)
        self.clone(result, self, deepcopy=True, memo=memo)
        return result