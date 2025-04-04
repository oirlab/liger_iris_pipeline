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

from .flat_field import FlatFieldStep
from .sky_subtraction import SkySubtractionImagerStep
from .dark_subtraction import DarkSubtractionStep
from .pipeline import Stage1Pipeline, ImagerStage2Pipeline, CreateFlatfield
from .dq_init import DQInitStep
from .normalize import NormalizeStep
from .parse_subarray_map import ParseSubarrayMapStep
from .merge_subarrays import MergeSubarraysStep
from .assign_wcs import AssignWCSStep
from .readout import NonlinearCorrectionStep, FitRampStep
from .combine_frames import CombineFramesStep
from .associations import L0Association, L1Association, L2Association