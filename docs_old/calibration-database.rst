***************************
Calibration
***************************

Calibration files
=================

Auxiliary data used in DRP algorithms are called calibration data. This includes both on-sky data (that is not of the astronomical target itself), daytime calibration frames, and other sub-component metadata. Metadata is non-image information that will typically come from the header of raw FITS files, or from IRIS, and/or the adaptive optics system via the observatory telemetry service. The NFIRAOS Science Calibration Unit (NSCU) will include a calibration system that will facilitate the taking of
daytime calibration frames, such as arc lamp spectra, white light flat field images, and pinhole grids for measuring distortion. 
The following table summarizes the required calibration files necessary for the Data Reduction Software.

Notes about the table: Note: * = SPEC only, PTG = pointing, D-Map = Distortion Map, Env = Environmental, DTC = Daytime calibration, NTC = Nightime calibration.

.. csv-table:: Calibration frames
   :header: "Name", "Reference Type", "Source", "Algorithms"
   :widths: 30,20,20,20

   "Atm. Dispersion Residual","Metadata",    "IRIS ADC",              "Atmospheric Correction"
   "Arc lamp spectra*",       "CAL (2D)",    "IRIS DTC (NSCU)",       "Wavelength solution "
   "Bad pixel map",           "CAL (2D)",    "IRIS DTC",              "Correction of detector artifacts"
   "Dark Frame",              "CAL (2D)",    "IRIS DTC and NTC",      "Dark subtraction "
   "Env metadata",            "Metadata",    "ESW, FITS header",      "All"
   "Fiber image",              "CAL (2D, 3D)","IRIS DTC (NSCU)",       "PSF Calibration"
   "Flux calibration star",   "CAL (2D, 3D)","IRIS On-sky",           "Extract Star, Remove Absorption Lines"
   "Instrument config",       "Metadata",    "ESW, FITS header",      "All"
   "Lenslet scan*",           "Rect Matrix CAL (2D)", "IRIS DTC (NSCU)","Spectral Extraction"
   "NFIRAOS config",          "Metadata",    "ESW, FITS header",      "All"
   "Pinhole Grid (D-Map)",    "CAL (2D)",    "IRIS DTC (NSCU)",       "Field distortion correction"
   "PSF metadata",            "Metadata ",   "ESW, FITS header",      "PSF calibration"
   "PSF star",                "CAL (2D, 3D)","IRIS on-sky ",          "PSF calibration"
   "Sky frame",               "CAL (2D, 3D)","IRIS on-sky",           "Sky-subtraction"
   "Telescope config PTG",    "Metadata ",   "ESW, FITS header",      "All "

.. csv-table:: Real time Calibration frames
   :header: "Name", "Reference Type", "Source", "Algorithms"
   :widths: 30,20,20,20

   "Atm. Dispersion Residual","Metadata",    "IRIS ADC",              "Atmospheric Correction"
   "Arc lamp spectra*",       "CAL (2D)",    "IRIS DTC (NSCU)",       "Wavelength solution "
   "Bad pixel map",           "CAL (2D)",    "IRIS DTC",              "Correction of detector artifacts"
   "Dark Frame",              "CAL (2D)",    "IRIS DTC and NTC",      "Dark subtraction "
   "Env metadata",            "Metadata",    "ESW, FITS header",      "All"
   "Instrument config",       "Metadata",    "ESW, FITS header",      "All"
   "NFIRAOS config",          "Metadata",    "ESW, FITS header",      "All"
   "Sky frame",               "CAL (2D, 3D)","IRIS on-sky",           "Sky-subtraction"
   "Telescope config PTG",    "Metadata ",   "ESW, FITS header",      "All "


Access calibration files via the Calibration Reference Data System (CRDS)
=========================================================================

The `Calibration Reference Data System
(CRDS) <https://hst-crds.stsci.edu/static/users_guide/overview.html>`_
is a set of tools developed by Space Telescope to organize and retrieve
calibration reference files, e.g. flat frames, dark frames, for JWST and
HST. When ``stpipe`` is executing a pipeline, it can automatically
connect to the JWST CRDS server and get the right flat based on the
metadata in the header of the data FITS files. The logic necessary to
choose the right file is encoded in text files. Those configuration
files and the actual calibration FITS files are also cached locally so
that the CRDS client library works even without any connection to a
central server.

We have created a CRDS cache folder in the Github repository
https://github.com/oirlab/tmt-crds-cache,
this includes in the ``mappings/tmt``
`folder <https://github.com/oirlab/tmt-crds-cache/tree/master/mappings/tmt>`_
the metadata for IRIS and the rules to choose the right flat-field and dark-current
frame, for now there are only dummy rules but this can be easily
customized querying the metadata in the input file.

Currently we do not have any CRDS server running, but the users can
download the CRDS cache locally and use it anyway, see the `Getting
started <getting-started>`_ documentation.

Also, the CRDS client library needs to have minimal knowledge about
metadata for TMT, therefore we maintain a fork of that library which
simply adds a submodule dedicated to IRIS, https://github.com/oirlab/tmt-crds, it is quite
easy to upgrade this to newer releases of CRDS by Space Telescope.

If TMT decided to use CRDS as their Data Management System, it would
leverage the extensive set of tools and documentation available and
would not require modifications to ``stpipe``; otherwise, we will
implement support for the DMS API into (our own fork of) ``stpipe``.

Structure of the files in CRDS
-------------------------------

The complete documentation of CRDS is available `from Space Telescope <https://jwst-crds.stsci.edu/static/users_guide/index.html>`_,
in this section we will provide a quick overview of the structure of the files in the CRDS cache we use for TMT/IRIS.

The files are all text files and have a hierarchical structure and the root is a ``.pmap`` file,
in our case it is `tmt_0001.pmap <https://github.com/oirlab/tmt-crds-cache/blob/master/mappings/tmt/tmt_0001.pmap>`_,
this file defines the observatory and it is used to switch between different versions of the instrument model.
In fact when we define the environment variables for CRDS we specify ``CRDS_CONTEXT`` to be the filename of
the ``.pmap`` file we want to use. This makes it very
easy to switch back and forth between different versions of the calibration files.

At the bottom of the ``.pmap`` file we point to all the different instruments of the current observatory and
the specific version of their definition files. For now we only have `tmt_iris_0003.imap <https://github.com/oirlab/tmt-crds-cache/blob/master/mappings/tmt/tmt_iris_0003.imap>`_.

The ``.imap`` file defines what kind of calibration files are available in CRDS. For example we can
have DARK, FLAT and MASK, each pointing to a reference file ``.rmap``.
The ``.rmap`` files are the most important because they actually encode the rules that the CRDS client uses
to choose which actual FITS calibration file should be used based on the metadata available in the
FITS header of the data file.
First in the ``parkey`` key of the header it defines what fields of the input file header should be taken
into consideration, for example the detector,  the subarray configuration and the datetime of the observation.
Then it encodes different rules to match for each value of the keys in ``parkey`` the filename of the
FITS calibration file that should be used. Those files are available as well in the CRDS cache inside
the `references folder <https://github.com/oirlab/tmt-crds-cache/tree/master/references/tmt/iris>`_.

Calibration FITS files are quite large, they are therefore stored on Github using ``Git LFS`` and are
automatically downloaded when a user clones the repository.
In production, scientists would just interface with the CRDS server and the local CRDS cache will be
automatically created and keep updated by synchronizing with the server. A Github repository with
the CRDS Cache is just useful during the development phase.

Retrieve files from the CRDS
----------------------------

Within ``liger_iris_pipeline``, all the subclasses of :py:class:`jwst.Step` can recall a configuration file using the
`self.get_reference_file` method and passing the input model (whose metadata will be used to find the right calibration file)
and the type of calibration file requested.

Or we could create a temporary :py:class:`jwst.Step` instance just to get the filename, for example::

    > raw_science_frame = liger_iris_pipeline.datamodels.IRISImageModel("raw_science_frame_sci.fits")
    > full_dark_filename = jwst.stpipe.Step().get_reference_file(raw_science_frame, "dark")
    > print(full_dark_filename)
    '~/crds_cache/references/tmt/iris/tmt_iris_dark_0001.fits'

Ingest new calibration files into CRDS
--------------------------------------

Users that would like to use a custom calibration file just occasionally can override them using options
to the calibration pipeline, see for example the ``override_flat`` configuration option to the flat-fielding
pipeline step.

Instead, developers that would like to add calibration files to the CRDS itself, and optionally provide a
pull request to the CRDS cache repository on Github, should use the ``crds`` command line tool.

1) Make sure that the calibration file has all the necessary headers defined,
if you are creating a file using ``liger_iris_pipeline`` this is automatically satisfied, for example using
:py:class:`IRISImageModel`.

2) Add any additional header key, typically ``USEAFTER``::

    USEAFTER= '2019-06-01 00:00:00'

3) Create the new ``.rmap`` file::

    crds refactor2 insert_reference --verbose --old-rmap \
        ~/crds_cache/mappings/tmt/tmt_iris_flat_0003.rmap --new-rmap \
        ~/crds_cache/mappings/tmt/tmt_iris_flat_0004.rmap \
        --instruments IRIS \
        --references path/to/new/reference/file.fits

4) Modify the ``.imap`` to point to this new file for the reference file we are working with

5) Run the ``update_checksums.sh`` in the ``mappings/tmt`` folder to automatically update the checksums

6) Add the FITS calibration file in the CRDS cache ``references/tmt/iris/`` folder

7) Optionally add all new files and modified files to the repository and send a Pull Request to the ``tmt-crds-cache`` repository
