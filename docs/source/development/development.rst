===========
Development
===========


Software infrastructure
-----------------------

liger_iris_pipeline relies on the infrastructure from Space Telescope Science Institute (STScI):

- :py:mod:`stdatamodels` + :py:mod:`asdf` specify the datamodel interface.
- :py:mod:`stpipe` specifies the interface for processing algorithms (steps) and pipelines.
- :py:mod:`stcal` provides generic algorithms for readout processing.
- :py:mod:`jwst` The JWST pipeline package which also implements the `stpipe` interface. It may provide algorithms appropriate to adopt for the Liger IRIS DRS.
- :py:mod:`astropy` The open source astropy package provides a wide variety of generic utilies for astronomical data processing.

datamodels
pipelines
steps

Below we provide additional information needed to extend the software infrastructure

.. toctree::
   :maxdepth: 2
   :glob:

   steps
   pipelines
   datamodels
   selectors