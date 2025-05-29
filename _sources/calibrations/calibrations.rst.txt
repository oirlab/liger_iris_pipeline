=====================
Calibrations and CRDS
=====================


Calibration files
-----------------

Many DRS algorithms require additional calibration data products or telemetries not stored with the data product itself. This includes both on-sky data (that is not of the astronomical target itself), daytime calibration frames, and other sub-component metadata. Metadata is non-image information that will typically come from the header of raw FITS files, or from IRIS, and/or the adaptive optics system via the observatory telemetry service. The NFIRAOS Science Calibration Unit (NSCU) will include a calibration system that will facilitate the taking of daytime calibration frames, such as arc lamp spectra, white light flat field images, and pinhole grids for measuring distortion.  The following table summarizes the required calibration files necessary for the Data Reduction Software.


CRDS
----

The `Calibration Reference Data System (CRDS) <https://hst-crds.stsci.edu/static/users_guide/overview.html>`_ is a set of tools developed by Space Telescope to organize, select, and retrieve calibration reference files. When a step or pipeline is executed, it first retrieves all calibration files associated with that science dataset and corresponding algorithms before applying them.

Mapping files
^^^^^^^^^^^^^

Mapping files are ascii files which specify the train of logic applied to match an observation with a reference file. They have a hierarchical structure:

#. ``.pmap`` files

``.pmap`` files govern all instruments for one project. They map a running pipeline to an instrument-specific mapping file. For liger_iris_pipeline, this is currently `ligeriri_0001.pmap <https://github.com/oirlab/liger-iris-crds-cache/blob/master/mappings/ligeriri/ligeriri_0001.pmap>`_. The top level ``pmap`` file is controlled by the environment variable ``CRDS_CONTEXT``.

#. ``.imap`` files

An instrument mapping file ``.imap`` is specific to one instrument. It will map to a ``.rmap`` file, which is a mapping file for a particular kind of reference file.

#. ``.rmap`` files

The ``.rmap`` files are arguably the most important because they actually encode the rules that the CRDS client uses to choose which actual FITS calibration file should be used based on the metadata available in the FITS header of the data file. The ``parkey`` key of the header defines what fields of the input file header should be taken into consideration, for example the detector (``meta.instrument.detector``),  the subarray configuration (``meta.subarray.name``) and the datetime of the observation (``meta.date``). How each field is used is then specified with the ``selector`` variable. 


Liger IRIS CRDS
---------------

For Liger and IRIS, we implement a custom (forked) version of CRDS called `liger_iris_crds <https://github.com/oirlab/liger_iris_crds>`_ which is contextually aware of Liger and IRIS data models. For now, this version of CRDS can only be operated in serverless mode where all calibrations are pre-cached. In future version, liger_iris_crds will interface with the Keck Observatory Archive (KOA) and the TMT data archive hosted at NOIRLab.

The Liger IRIS DRS also uses a `CRDS cache folder <https://github.com/oirlab/liger-iris-crds-cache>`_ to store all mapping and reference files. This cache currently includes all mapping files and references used in the DRS and lives on a user's (developer's) local machine. The rulesets for matching Liger and IRIS calibrations are limtied and will be developed with the rest of the DRS.

Calibration FITS files are quite large and are therefore stored with ``Git LFS``. They are automatically downloaded when a user clone's the liger-iris-crds-cache repo. In production, users will instead interface with the appropriate CRDS server and the local CRDS cache will be automatically created and is synced with the server (cached calibrations are limited to a user's dataset).


Retrieve files from the CRDS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Within ``liger_iris_pipeline``, all the subclasses of :py:class:`~liger_iris_pipeline.base_step.LigerIRISStep` can retrieve calibration file using the instance method :meth:`~liger_iris_pipeline.base_step.LigerIRISStep.get_reference_file` and passing the input model (whose metadata will be used to find the right calibration file) and the type of calibration file requested.

Or we could create a temporary :py:class:`~liger_iris_pipeline.base_step.LigerIRISStep` instance just to get the filename, for example::

    > raw_science_frame = liger_iris_pipeline.datamodels.ImagerModel("2024B-P123-008_IRIS_IMG1_SCI-J1458+1013-Y-4.0_LVL1_0001-00.fits")
    > full_dark_filename = liger_iris_pipeline.LigerIRISStep().get_reference_file(raw_science_frame, "dark")
    > print(full_dark_filename)
    '~/crds_cache/references/ligeriri/iris/IRIS_IMG1_DARK_20240924T000000_0.0.1.fits'


Ingest new calibration files into CRDS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Users that would like to use a custom calibration file can specify them using options to the calibration pipeline, see for example the ``flat`` configuration option to the flat-fielding pipeline step. If a user would like to formally make a calibration file available through CRDS, the following steps can be taken:

1. Make sure that the calibration file has all the necessary headers defined, if you are creating a file using ``liger_iris_pipeline`` this is automatically satisfied, for example using :py:class:`~liger_iris_pipeline.datamodels.imager.ImagerModel`.

2. Create the new ``.rmap`` file::

    crds refactor2 insert_reference --verbose --old-rmap \
        ~/crds_cache/mappings/ligeriri/ligeriri_iris_flat_0001.rmap --new-rmap \
        ~/crds_cache/mappings/ligeriri/ligeriri_iris_flat_0002.rmap \
        --instruments IRIS \
        --references path/to/new/reference/file.fits

3. Modify the ``.imap`` to point to this new ``.rmap`` for the reference file we are working with.

4. Run the ``update_checksums.sh`` in the ``mappings/ligeriri`` folder to automatically update the checksums.

5. Add the FITS calibration file in the CRDS cache ``references/ligeriri/iris/`` folder.

6. Optionally add all new files and modified files to the repository and send a Pull Request to the ``liger-iris-crds-cache`` repository.


List of Calibrations
--------------------

See :doc:`../datamodels/datamodels` for additional details on each calibration. "Real Time" indicates whether or not the reference file can be acquired and created during on-sky operations.

.. csv-table::
   :header: "Name", "Reference Type", "Source", "Algorithms", "Real Time?"

   "Atm. Dispersion Residual","Metadata","IRIS ADC","Atmospheric Correction","Yes"
   "Arc lamp spectra*", "CAL (2D)","IRIS DTC (NSCU)","Wavelength solution ","Yes"
   ":py:class:`~liger_iris_pipeline.datamodels.dq.DQModel`","CAL (2D)","IRIS DTC","Correction of detector artifacts","Yes"
   ":py:class:`~liger_iris_pipeline.datamodels.dark.DarkModel`","CAL (2D)","IRIS DTC and NTC","Dark subtraction ","Yes"
   ":py:class:`~liger_iris_pipeline.datamodels.flat.FlatModel`","CAL (2D)","IRIS DTC and NTC","Flatfield correction","Yes"
   "Env metadata", "Metadata","ESW, FITS header","All","Yes"
   "Fiber image", "CAL (2D, 3D)","IRIS DTC (NSCU)","PSF Calibration","No"
   "Flux calibration star","CAL (2D, 3D)","IRIS On-sky","Extract Star, Remove Absorption Lines","No"
   "Instrument config","Metadata","ESW, FITS header","All","Yes"
   "Lenslet scan*", "Rect Matrix CAL (2D)","IRIS DTC (NSCU)","Spectral Extraction","No"
   "NFIRAOS config", "Metadata","ESW, FITS header","All","Yes"
   "Pinhole Grid (D-Map)","CAL (2D)","IRIS DTC (NSCU)","Field distortion correction","No"
   "PSF metadata","Metadata ","ESW, FITS header","PSF calibration","No"
   "PSF star","CAL (2D, 3D)","IRIS on-sky ","PSF calibration","No"
   "Sky frame","CAL (2D, 3D)","IRIS on-sky","Sky-subtraction","Yes"
   "Telescope config PTG","Metadata","ESW,FITS header","All", "Yes"