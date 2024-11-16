from astropy.time import Time
from stdatamodels import DataModel

__all__ = ["LigerIRISDataModel"]

class LigerIRISDataModel(DataModel):
    """
    The base data model for Liger and IRIS.
    This class should not be instantiated on its own.
    """
    schema_url = "https://oirlab.github.io/schemas/LigerIRISDataModel.schema"

    @property
    def crds_observatory(self):
        return "ligeriri" # NOTE: Change this after tests pass again.
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
        self.meta.origin.time = Time.now().isot