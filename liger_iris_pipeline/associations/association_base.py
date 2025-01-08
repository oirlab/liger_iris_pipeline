# https://jwst-pipeline.readthedocs.io/en/latest/jwst/associations/association_reference.html#ref-asn-core-methods
from jwst.associations import Association
from .. import datamodels
from pathlib import Path
import json
from datetime import datetime

__all__ = ['LigerIRISAssociation']

class LigerIRISAssociation(Association):
    """
    IRIS Association base class.
    NOTE: This is a crude implementation to get the DRS to run smoothly while developing.
    TODO: Rulesets and a better interface will be added later.
    """

    def __init__(self, data : dict | None = None):
        #super().__init__(*args, **kwargs)
        self.data = {}
        self.data["name"] = self.__class__.__name__ + datetime.now().strftime("%Y%m%dT%H%M%S")
        self.data["asn_rule"] = self.__class__.__name__
        self.data["asn_type"] = self.__class__.__name__
        self.data["asn_pool"] = "pool" # TODO: Invetigate if we need this?
        self.data["products"] = []
        if data is not None:
            self.data.update(data)

    @classmethod
    def load(cls, filename : str | Path):
        with open(str(filename), "r") as f:
            return cls(json.load(f))
        

    @staticmethod
    def load_as_json(cls, filename : str | Path):
        with open(str(filename), "r") as f:
            return json.load(f)

    @property
    def products(self):
        return self.data["products"]
    

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
    
    @classmethod
    def from_member(cls, member : str | datamodels.LigerIRISDataModel):
        input_model = datamodels.open(member)
        product = {
            "members": [
                {
                    "expname": input_model.filename,
                    "exptype": input_model.meta.exposure.type,
                },
            ]
        }
        return cls.from_product(product)
    
    @property
    def name(self):
        return self.data["name"]