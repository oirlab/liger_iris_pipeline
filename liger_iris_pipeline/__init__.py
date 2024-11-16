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

from .flatfield import FlatFieldStep
from .background import BackgroundStep
from .dark_current import DarkCurrentStep
from .pipeline import ProcessFlatfield, ImagerStage2Pipeline
from .dq_init import DQInitStep
from .normalize import NormalizeStep
from .parse_subarray_map import ParseSubarrayMapStep
from .merge_subarrays import MergeSubarraysStep
from .assign_wcs import AssignWcsStep
