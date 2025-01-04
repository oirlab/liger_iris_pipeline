import os
from collections import defaultdict

from stpipe import Pipeline
from ..base_step import LigerIRISStep
from pathlib import Path
from ..associations import LigerIRISAssociation, load_asn

__all__ = [
    "LigerIRISPipeline"
]

class LigerIRISPipeline(Pipeline, LigerIRISStep):

    default_association : LigerIRISAssociation = None
    
    def input_to_asn(self, input):
        """
        Convert input to an association.
        TODO: Add case for LigerIRISDataModel

        Parameters:
            input (str | Path | LigerIRISAssociation): The input file.

        Returns:
            LigerIRISAssociation: An instance of the appropriate LigerIRISAssociation.
        """

        # Input already is an association
        if isinstance(input, LigerIRISAssociation):
            return input
        
        # Input is a file
        if isinstance(input, str | Path):
            input = str(input)
            if os.path.splitext(input)[1] == '.json': # Association file
                asn = load_asn(input)
            else:
                asn = self.default_association.from_member(input) # DataModel file
        elif isinstance(input, dict):
            asn = self.default_association.from_product(input) # Single product (dict)
        else:
            raise ValueError(f"Input type {type(input)} not supported.")
        
        return asn
    
    @staticmethod
    def asn_product_by_types(exp_product : dict):
        """
        Get the members of an exposure product by type.

        Parameters:
            exp_product (dict): The exposure product.

        Returns:
            dict: The members of the exposure product by type.
        """
        members_by_type = defaultdict(list)
        for member in exp_product["members"]:
            members_by_type[member["exptype"].lower()].append(member["expname"])
        return members_by_type