import os
from pathlib import Path

from astropy.time import Time
from astropy.io import fits
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
            self.filename = str(init)
        else:
            self.filename = None

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
        elif isinstance(self.meta.filename, str | Path) and isinstance(init, str | Path):
            if self.meta.filename != str(init):
                self.meta.filename = str(init)
        self.meta.date_created = Time.now().isot

    @property
    def filename(self):
        return self._filename
        
    @filename.setter
    def filename(self, value):
        self.filename = value

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
    def generate_filename(
        instrument : str,
        obsid : str,
        detector : str, obstype : str, level : int | str = 0,
        exp : int | str = '0001', subarray : int | str | None = None
    ):
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
        return f"{obsid}_{instrument}_{detector.upper()}_{obstype}_LVL{int(level)}_{exp}{subarray}.fits"

    def get_primary_array_name(self):
        return 'DATA'