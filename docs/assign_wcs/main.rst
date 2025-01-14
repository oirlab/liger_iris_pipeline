
Description
===========

``assign_wcs`` associates a WCS object with each science exposure. The WCS object transforms
positions in the detector frame to positions in a world coordinate frame - ICRS and wavelength.
In general there may be intermediate coordinate frames depending on the instrument.
The WCS is saved in the ASDF extension of the FITS file. It can be accessed as an attribute of
the meta object when the fits file is opened as a data model.

Currently IRIS implements a very simple model that expects standard FITS WCS keywords in the
header and uses ``astropy.modeling`` to build a transformation pipeline, wrap it into
a ``gwcs.WCS`` object and store it as ``output_model.meta.wcs``, as it is expected
by Level 3 pipelines.

The forward direction of the transforms is from detector to world coordinates
and the input positions are 0-based.

``assign_wcs`` expects to find the basic WCS keywords in the
SCI header. Distortion and spectral models are not implemented yet and will be stored in reference files in the
`ASDF <http://asdf-standard.readthedocs.org/en/latest/>`__  format.

Example
-------

See an example script to process a file with FITS WCS keywords in the header::

    import liger_iris_pipeline
    import astropy.units as u

    input_filename ="iris_sim_gc_filterKN3_fix.fits"
    output = liger_iris_pipeline.assign_wcs.AssignWCSStep.call(input_filename)
    print(output.meta.wcs([0,4096]*u.pix,[0,4096]*u.pix))
