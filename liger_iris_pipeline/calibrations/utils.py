

def get_calibration_selector_type(name : str):
    """
    Get a CalibrationSelector class by name.

    Parameters
    ----------
    name : str
        The name of the CalibrationSelector class.

    Returns
    -------
    type[CalibrationSelector]
        The CalibrationSelector class.
    """
    from . import SELECTOR_REGISTER
    if name not in SELECTOR_REGISTER:
        raise ValueError(f"CalibrationSelector '{name}' not found.")
    return SELECTOR_REGISTER[name]