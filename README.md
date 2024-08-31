Data Reduction System (DRS) for the Thirty Meter Telescope IRIS imager/spectrograph
-----------------------------------------------------------------------------------

[![Powered by Astropy](http://img.shields.io/badge/powered%20by-AstroPy-orange.svg?style=flat)](http://astropy.org)
![Github action test](https://github.com/oirlab/iris_pipeline/workflows/Python%20package/badge.svg)

Data Reduction System (DRS) for the instrument [IRIS (InfraRed Imaging Spectrometer)](https://oirlab.ucsd.edu/IRIS.html), IRIS is a first light instrument for the [TMT (Thirty Meter Telescope)](https://tmt.org) observatory.

The DRS pipeline is based on [JWST' pipeline tool `stpipe`](https://github.com/spacetelescope/jwst).

Documentation
-------------

[oirlab.github.io/iris-pipeline](https://oirlab.github.io/iris-pipeline)


License
-------

This project is Copyright (c) Andrea Zonca, Arun Surya and licensed under
the terms of the BSD 3-Clause license. This package is based upon
the `Astropy package template <https://github.com/astropy/package-template>`_
which is licensed under the BSD 3-clause licence.

Testing Data
------------

### Imager

#### raw_frame_flat_20240805.fits
- Raw flat field image
- https://figshare.com/articles/dataset/IRIS_Liger_DRS_Test_Data/26492029?file=48191521

#### raw_frame_dark_20240805.fits
- Raw dark image
- https://figshare.com/articles/dataset/IRIS_Liger_DRS_Test_Data/26492029?file=48191518

#### raw_readout_20240805.fits
- Raw readouts (4D array)
- https://figshare.com/articles/dataset/IRIS_Liger_DRS_Test_Data/26492029?file=48191977

#### raw_frame_sci_20240805.fits
- Raw science frame of a few stars
- https://figshare.com/articles/dataset/IRIS_Liger_DRS_Test_Data/26492029?file=48191524

#### raw_background_20240829.fits
- Raw (sky) background frame
- https://figshare.com/articles/dataset/IRIS_Liger_DRS_Test_Data/26492029?file=48903439

#### test_iris_subtract_bg_flat_cal_20240822.fits
- Processed Level 2 image data
- https://figshare.com/articles/dataset/IRIS_Liger_DRS_Test_Data/26492029?file=48737014

#### reduced_science_frame_sci_subarray_1_20240831.fits
- Subarray image
- https://figshare.com/articles/dataset/IRIS_Liger_DRS_Test_Data/26492029?file=48911917

#### reduced_science_frame_sci_subarray_2_20240831.fits
- Subarray image
- https://figshare.com/articles/dataset/IRIS_Liger_DRS_Test_Data/26492029?file=48911914

#### reduced_science_frame_sci_with_subarrays_20240831.fits
- Starting point for merging subarrays 1 & 2 above with nans where subarrays are
- https://figshare.com/articles/dataset/IRIS_Liger_DRS_Test_Data/26492029?file=48911932