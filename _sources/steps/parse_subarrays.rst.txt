Parse Subarray Map
==================


Overview
--------

The step is only useful for full raw science frames which have been acquired concurrently with subarrays. This step parses the extension ``SUBARR_MAP`` and determines the parameters defining each specified subarray. These parameters are copied it into ImagerModel.meta.subarray_map, which is a ASDF-based property in the FITS file which encodes the metadata of the subarrays as a list of dictionaries.

Each subarray is processed separately and the full science frame is also acquired and has missing values at the location of each of the subarrays (up to 10) which are currently being acquired.

The raw science frame from the detector has a dedicated FITS extension that encodes the location of the subarrays, i.e. has zeros everywhere, then a rectangle of 1 at the location of subarray 1, a rectangle of 2 at the location of subarray 2 and so on. Subarrays cannot overlap.

**Class**: :py:class:`~liger_iris_pipeline.parse_subarray_map.parse_subarray_map_step.ParseSubarrayMapStep`


Algorithm
---------

The locations of each subarray are determined with ``numpy.where`` from the extension ``SUBARR_MAP`` and are stored in the header as ``ImagerModel.meta.subarray_map``, which is a ASDF-based property in the FITS file which encodes the metadata of the subarrays as a list of dictionaries::

    ImagerModel.meta.subarray_map = [{"xstart":80, "ystart":70, "xsize":10, "ysize":10}, {"xstart":10, "ystart":20, "xsize":20, "ysize":20}]

It also raises 1 bit of the data quality flag ``dq`` so that the algorithms which filter out bad data, e.g. when taking ``mean`` or ``median``, automatically filters them out. The bit used for that is ``SUBARRAY_DQ_BIT`` in ``parse_subarray_map_step.py``. (NOTE: Elaborate on this).


Arguments
---------

**input** : ``str`` | :py:class:`~liger_iris_pipeline.datamodels.imager.ImagerModel`
    The input file or imager model to process.

Subarrays
---------

TBD

Calibration Files
-----------------

None.