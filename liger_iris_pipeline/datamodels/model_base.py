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

        # Get the schema from instrument name
        if instrument is not None:
            self.set_schema_from_instrument(instrument)
        elif isinstance(init, str | Path):
            self.set_schema_from_fits_filename(init)
        elif isinstance(init, fits.HDUList):
            self.set_schema_from_hdulist(init)
        
        # Call super with schema_url now set
        super().__init__(init=init, **kwargs)

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
        instrument = init[0].header['INSTRUME']
        self.set_schema_from_instrument(instrument)
        
    def __setattr__(self, attr, value): # :)
        if attr == 'schema_url':
            self.__dict__[attr] = value
        else:
            super().__setattr__(attr, value)


    @property
    def crds_observatory(self):
        return "ligeriri"
    #     """
    #     The CRDS observatory for this model.

    #     Returns:
    #     str : the CRDS observatory.  Returns "wmko" for Liger, and "tmt" for IRIS.
    #     """
    #     if self.telescope is None:
    #         return None
    #     tel = self.telescope.lower()
    #     if tel == "wmko":
    #         return "wmko"
    #     elif tel == "tmt":
    #         return "tmt"
    #     else:
    #         raise ValueError(f"Property `datamodel.instrument` invalid for {self}: {self.instrument}")


    @property
    def telescope(self):
        return self.meta.telescope
    
    @property
    def instrument(self):
        return self.meta.instrument.name
    

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
        self.meta.date = Time.now().isot