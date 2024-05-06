# Licensed under a 3-clause BSD style license - see LICENSE.rst

# ----------------------------------------------------------------------------

# Enforce Python version check during package import.
# This is the same check as the one at the top of setup.py
import sys

__version__ = "0.5.dev"
__minimum_python_version__ = "3.6"


class UnsupportedPythonError(Exception):
    pass


if sys.version_info < tuple(
    (int(val) for val in __minimum_python_version__.split("."))
):
    raise UnsupportedPythonError(
        "iris_pipeline does not support Python < {}".format(__minimum_python_version__)
    )

from .flatfield import *
from .background import *
from .pipeline import *
from .dq_init import *
from .normalize import *
from .parse_subarray_map import *
from .merge_subarrays import *
from .assign_wcs import *

from .datamodels import  monkeypatch_jwst_datamodels
