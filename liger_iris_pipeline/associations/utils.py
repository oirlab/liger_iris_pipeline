import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

def load_asn(asn_file : str):
    """
    Load an association file and return the association object.
    """
    asn_class = class_from_association_type(asn_file)
    try:
        return asn_class.load(asn_file)
    except Exception:
        log.error(f"Could not load association file {asn_file}")
        raise


def class_from_association_type(init):
    """
    Get the association type from the association file header.

    Parameters:
    init (str): The ASN filename.

    Returns:
    type | None: The LigerIRISAssociation class if found.
    """

    from . import DEFINED_ASSOCIATIONS
    from . import LigerIRISAssociation
    asn = LigerIRISAssociation.load_as_json(init)
    class_name = asn['asn_type']
    if class_name in DEFINED_ASSOCIATIONS:
        _class = DEFINED_ASSOCIATIONS[class_name]
    else:
        log.error(f"Association type {class_name} not found in DEFINED_ASSOCIATIONS")
        _class = None
    return _class