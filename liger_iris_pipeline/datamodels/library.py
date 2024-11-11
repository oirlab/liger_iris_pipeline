import io

import asdf
from astropy.io import fits
from .util import datamodels_open
from stpipe.library import AbstractModelLibrary

from jwst.associations import AssociationNotValidError, load_asn

__all__ = ["ModelLibrary"]


class ModelLibrary(AbstractModelLibrary):
    """
    Liger implementation of the ModelLibrary, a container designed to allow
    efficient processing of datamodel instances created from an associations.
    See the `stpipe library documentation <https://stpipe.readthedocs.io/en/latest/model_library.html`
    for details.
    """
    @property
    def crds_observatory(self):
        return "ligeriri"
    
    @property
    def exptypes(self):
        """
        List of exposure types for all members in the library.
        """
        return [member["exptype"] for member in self._members]
    
    def indices_for_exptype(self, exptype):
        """
        Determine the indices of models corresponding to `exptype`.

        Parameters:
        exptype (str): Exposure type as defined in an association, e.g. "science". case-insensitive

        Returns:
        ind (list): Indices of models in ModelLibrary with member exposure types matching `exptype`.

        Notes:
        Library does NOT need to be open (i.e., this can be called outside the `with` context).
        """
        return [i for i, member in enumerate(self._members) if member["exptype"].lower() == exptype.lower()]

    def _model_to_filename(self, model):
        model_filename = model.meta.filename
        if model_filename is None:
            model_filename = "model.fits"
        return model_filename

    def _datamodels_open(self, filename, **kwargs):
        return datamodels_open(filename, **kwargs)

    @classmethod
    def _load_asn(cls, asn_path):
        try:
            with open(asn_path) as asn_file:
                asn_data = load_asn(asn_file)
        except AssociationNotValidError as e:
            raise OSError("Cannot read ASN file.") from e
        return asn_data

    def _assign_member_to_model(self, model, member):
        for attr in ("group_id", "tweakreg_catalog", "exptype"): # NOTE: Limit to exptype?
            if attr in member:
                setattr(model.meta, attr, member[attr])
        if not hasattr(model.meta, "asn"):
            model.meta["asn"] = {}

        if "table_name" in self.asn.keys():
            setattr(model.meta.asn, "table_name", self.asn["table_name"])

        if "asn_pool" in self.asn.keys(): # do not clobber existing values
            setattr(model.meta.asn, "pool_name", self.asn["asn_pool"])