
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension(
        name="liger_iris_pipeline.ramp_fitting.fitramp_cython_Brandt",
        sources=["liger_iris_pipeline/ramp_fitting/fitramp_cython_Brandt.pyx"],
        include_dirs=[np.get_include()],
    )
]

setup(
    ext_modules=cythonize(
        extensions,
        language_level=3,
    )
)
