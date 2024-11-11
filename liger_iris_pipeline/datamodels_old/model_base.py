from astropy.time import Time

from stdatamodels.jwst.datamodels import JwstDataModel as _DataModel


__all__ = ["LigerIrisDataModel"]


class LigerIrisDataModel(_DataModel):

    schema_url = "https://oirlab.github.io/schemas/liger_iris_core.schema"

    @property
    def crds_observatory(self):
        """
        Get CRDS observatory code for this model.

        Returns
        -------
        str
        """
        return "ligeriri"

    def get_crds_parameters(self):
        """
        Get parameters used by CRDS to select references for this model.

        Returns
        -------
        dict
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
