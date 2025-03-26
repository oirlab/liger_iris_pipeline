.. _parse_subarray_map_step:

==================
Parse Subarray Map
==================

Description
===========

SUBARR_MAP extension
--------------------

This pipeline step is only useful for full raw science frames which
have been acquired concurrently with subarrays.

Each subarray is processed separately and the full science frame is
also acquired and has missing values at the location of each of
the subarrays (up to 10) which are currently being acquired.

The raw science frame from  the detector has a dedicated FITS extension
that encodes the location of the subarrays, i.e. has zeros everywhere,
then a rectangle of 1 at the location of subarray 1, a rectangle of 2
at the location of subarray 2 and so on. Subarrays cannot overlap.

Parse subarray map extension
----------------------------

This step gets the information from this extension and duplicates it
into the header as `IRISImageModel.meta.subarray_map`,
which is a ASDF-based property in the FITS file which encodes the metadata
of the subarrays as a list of dictionaries::

    IRISImageModel.meta.subarray_map = [{"xstart":80, "ystart":70, "xsize":10, "ysize":10}, {"xstart":10, "ystart":20, "xsize":20, "ysize":20}]

It also raises 1 bit of the data quality flag `dq` so that the algorithms which
filter out bad data, e.g. when taking `mean` or `median`, automatically filters
them out. The bit used for that is `SUBARRAY_DQ_BIT` in `parse_subarray_map_step.py`.

.. automodapi:: liger_iris_pipeline.parse_subarray_map
