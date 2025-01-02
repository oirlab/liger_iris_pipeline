# https://jwst-pipeline.readthedocs.io/en/latest/jwst/associations/association_reference.html#ref-asn-core-methods
from jwst.associations import Association
from pathlib import Path
import json

class LigerIRISAssociation(Association):
    """
    IRIS Association base class.
    NOTE:
        This is a crude implementation to get the DRS to run smoothly while developing.
        Rulesets will be added later.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["asn_rule"] = self.__class__.__name__
        self["asn_type"] = self.__class__.__name__
        self["asn_pool"] = "pool" # TODO: Invetigate if we need this?
        self["products"] = []

    @classmethod
    def load(self, filename : str | Path):
        with open(str(filename), "r") as f:
            return json.load(f)

    @property
    def products(self):
        return self["products"]
    
    def add(self, item):
        self.products.append(item)
        return True, self.products
    
    def dump(self, filename : str | Path):
        with open(str(filename), "w") as f:
            json.dump(self.data, f)

    @classmethod
    def from_product(cls, product : dict):
        asn = cls()
        asn.add(product)
        return asn