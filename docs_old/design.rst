IRIS Data Reduction System design
=================================

Purpose
=======

The IRIS Data Reduction System is planned to perform:

-  real-time (< 1 minute) and offline data processing of IRIS images and
   spectroscopic data with the
   :py:mod:`liger_iris_pipeline` Python
   package based on JWST’s pipeline package
   ``stpipe``, see `the documentation <https://jwst-pipeline.readthedocs.io/en/latest/jwst/stpipe/>`_
-  raw readout processing from the IRIS imager and spectrograph into raw
   science quality frames with the C library
   ``iris_readout`` at https://github.com/oirlab/iris_readout, which
   will be used directly during real-time operations and will be wrapped
   into Python modules in ``liger_iris_pipeline`` for offline processing.
-  visualization of raw and reduced data to facilitate data assessment
   and analysis for real-time and offline use. These tools will be
   developed later and will possibly be based on existing community
   software tools like `DS9 <http://ds9.si.edu/site/Home.html>`_ or
   `cubeviz <https://cubeviz.readthedocs.io/>`_.

Software infrastructure
=======================

We rely on the excellent work mostly by Space Telescope to grow the
Python in Astronomy ecosystem around the ``astropy`` package. They also
developed a suite of open-source tools to operate JWST based on their
experience operating the Hubble Space telescope.

The :py:mod:`jwst` Python package
bundles several tools:

-  a :py:mod:`jwst.datamodel` package to handle custom schemas for complex
   hierarchical metadata
-  a :py:mod:`stpipe` package to configure and execute processing pipelines
-  a large array of data processing modules to analyze data from all
   instruments on board of JWST

We leverage this effort by:

-  building a custom schema for IRIS
-  using ``stpipe`` to execute our pipelines
-  starting from JWST processing modules and customizing them for IRIS
   and publishing them on the ``liger_iris_pipeline``
   repository https://github.com/oirlab/liger_iris_pipeline.

Processing levels and data product stages
=========================================

Similar to how `JWST has organized their pipeline <https://jwst-pipeline.readthedocs.io/en/latest/jwst/data_products/stages.html>`_, we also organize pipelines and data products in stages.

* Level 0 data products are the FITS files containing the individual raw readouts
* Level 1 pipelines, backed by ``iris_readout``, combine the raw readouts and apply data quality checks and cuts. In production at the Observatory, this will be performed directly by the detector C software (HCD).
* The Level 1 pipelines produce level 1 data products, the "raw science frames", still uncalibrated.
* Level 2 pipelines apply calibration, flat-fielding and more to raw science frames
* The output are the Level 2 data products "reduced science frames"
* Multiple "reduced science frames" can be combined together by a Level 3 pipeline, for example for mosaicking.
* The outputs of Stage 3 pipelines are Level 3 data products.