.. _pipelines:

Pipeline Stages
===============

End-to-end calibration of TMT data is divided into 3 main stages of
processing, currently we mirror the JWST nomenclature, eventually we will
adapt to TMT:

- Stage 1 consists of detector-level corrections that are performed on a
  group-by-group basis, followed by ramp fitting. The output of stage 1
  processing is a countrate image per exposure, or per integration for
  some modes. Details of this pipeline can be found at:

  - `detector1` (`work in progress <https://github.com/oirlab/liger_iris_pipeline/pull/7>`_)

- Stage 2 processing consists of additional instrument-level and
  observing-mode corrections and calibrations to produce fully calibrated
  exposures. The details differ for imaging and spectroscopic exposures,
  and there are some corrections that are unique to certain instruments or modes.
  Details are at:

  - :ref:`image2`
  - `spec2` (not implemented yet)

- Stage 3 processing consists of routines that work with multiple exposures
  and in most cases produce some kind of combined product.
  There are unique pipeline modules for stage 3 processing of
  imaging, spectroscopic, coronagraphic, AMI, and TSO observations.
  *None implemented yet*.

In addition, there are several pipeline modules designed for special instrument or
observing modes, including:

- :ref:`preprocess_flatfield <preprocess_flatfield>` for processing dark exposures

Pipeline Classes and Configuration Files
========================================

Each pipeline consists of a certain sequence of calibration steps and is
defined as a Python class within a Python code module. The pipelines
can be executed from the command line either by referencing their class name or
by supplying a configuration (.cfg) file that in turn references the pipeline class
.
From within Python, the pipelines are called by their class names, but
configuration files can still be supplied in order to set pipeline or step
parameter values.
The table below lists the pipeline classes that are currently available, the
corresponding configuration files that call those classes, and
the observing modes for which they are intended. Note that there are some
pipeline modules that are referenced by more than one configuration file.


+---------------------------------------------------------+---------------------------+------------------------------+
| Pipeline Class                                          | Configuration File        | Used For                     |
+=========================================================+===========================+==============================+
| `~liger_iris_pipeline.pipeline.ProcessImagerL2Pipeline` | image2.cfg                | Stage 2: imaging modes       |
+---------------------------------------------------------+---------------------------+------------------------------+

Pipelines vs. Exposure Type
===========================

The data from different observing modes needs to be processed with
different combinations of the pipeline stages listed above. The proper pipeline
selection is usually based solely on the exposure type (EXP_TYPE keyword value).
Some modes, however, require additional selection criteria, such as whether the
data are to be treated as Time-Series Observations (TSO). Some EXP_TYPEs are
exclusively TSO, while others depend on the value of the TSOVISIT keyword.
The following table lists the pipeline modules that should get applied to various
observing modes, based on these selectors. Exposure types that do not allow TSO
mode are marked as "N/A" in the TSOVISIT column.

*Table to be created for IRIS*

+---------------------+----------+-------------------+-----------------------+------------------+
| | EXP_TYPE          | TSOVISIT | Stage 1 Pipeline  | Stage 2 Pipeline      | Stage 3 Pipeline |
+=====================+==========+===================+=======================+==================+
+---------------------+----------+-------------------+-----------------------+------------------+

