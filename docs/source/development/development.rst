Development
===========


Purpose
-------

The Liger IRIS Data Reduction System will perform:

- Real-time (< 1 minute) and offline data processing of Liger/IRIS imager and IFS data.
- Visualization of raw and reduced data to facilitate data assessment and analysis for real-time and offline use. These tools will be developed later and will possibly be based on existing community software tools like `DS9 <http://ds9.si.edu/site/Home.html>`_ or `cubeviz <https://cubeviz.readthedocs.io/>`_.


Software infrastructure
-----------------------

We rely on the infrastructure from Space Telescope Science Institute (STScI):

- :py:mod:`stdatamodels` + :py:mod:`asdf` specify the datamodel interface.
- :py:mod:`stpipe` specifies the interface for processing algorithms (steps) and pipelines.
- :py:mod:`stcal` provides generic algorithms for readout processing.
- :py:mod:`jwst` The JWST pipeline package which also implements the `stpipe` interface. It may provide algorithms appropriate to adopt for the Liger IRIS DRS.
- :py:mod:`crds` The Calibraiton Reference Database System (CRDS) is a package to specify logic for matching science observations with reference files. CRDS provides a server client utilities specific to JWST (and other STScI missions) which will eventually be replaced by the appropriate interfaces for Keck and TMT.
- :py:mod:`astropy` The open source astropy package provides a wide variety of generic utilies for astronomical data processing.

The Liger IRIS DRS is implemented as a Python package with the following structure:

- :py:mod:`liger_iris_pipeline`  package defines the Liger and IRIS datamodels, steps, and pipelines.
- :py:mod:`liger_iris_crds` package defines the CRDS logic for Liger and IRIS.


.. toctree::
   :maxdepth: 2
   :glob:

   datamodels
   steps_pipelines