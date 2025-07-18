# Licensed under a 3-clause BSD style license - see LICENSE.rst

# ----------------------------------------------------------------------------

# Enforce Python version check during package import.
# This is the same check as the one at the top of setup.py
import sys

try:
    from setuptools_scm import get_version
    __version__ = get_version(root="..", relative_to=__file__)
except ImportError:
    __version__ = "unknown"

__minimum_python_version__ = "3.11"


class UnsupportedPythonError(Exception):
    pass


if sys.version_info < tuple(
        (int(val) for val in __minimum_python_version__.split("."))
    ):
    raise UnsupportedPythonError(
        "iris_pipeline does not support Python < {}".format(__minimum_python_version__)
    )

from .flat_field import *
from .background import *
from .dark_subtraction import *
from .pipeline import *
from .dq_init import *
from .normalize import *
from .parse_subarray_map import *
from .merge_subarrays import *
from .assign_wcs import *
from .readout import *
from .combine_frames import *