# Licensed under a 3-clause BSD style license - see LICENSE.rst

# ----------------------------------------------------------------------------

# Enforce Python version check during package import.
# This is the same check as the one at the top of setup.py
import sys

# try:
#     from setuptools_scm import get_version
#     __version__ = get_version(root="..", relative_to=__file__)
# except ImportError:
#     __version__ = "unknown"

try:
    from ._version import version as __version__
except ImportError:
    try:
        from setuptools_scm import get_version
        __version__ = get_version(root="..", relative_to=__file__)
    except (ImportError, LookupError):
        __version__ = "unknown"

__minimum_python_version__ = "3.12"


class UnsupportedPythonError(Exception):
    pass


if sys.version_info < tuple(
        (int(val) for val in __minimum_python_version__.split("."))
    ):
    raise UnsupportedPythonError(
        "iris_pipeline does not support Python < {}".format(__minimum_python_version__)
    )

from . import _yaml_config
# from .detector_flat import *
# from .background import *
# from .dark_subtraction import *
# from .pipeline import *
# from .dq_init import *
# from .normalize import *
# from .parse_subarray_map import *
# from .jump_detection import *
# from .merge_subarrays import *
# from .assign_wcs import *
# from .ramp_fitting import *
# from .nonlinear_correction import *
# from .gain import *
# from .saturation import *
# from .bias_subtraction import *
# from .coadd import *
# from .refpix import *
# from .distortion import *
# from .calibrations import RegisterCalibrationStep