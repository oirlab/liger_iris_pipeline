=============
Cube Assembly
=============

Description
-----------

TBD.


Algorithm
---------

The spectral data cubes are assembled in this algorithm. The algorithm takes each extracted spectrum from spectral extraction routine and maps them to an x, y position on the sky (spatial rectification) based on the WCS information, and their z positions are shifted based on their individual wavelength solutions. The data cube format is (x, y, wavelength), which is common among data cubes with wavelength and frequency (i.e. VLT/SINFONI, ALMA and VLA).


Subarrays
---------

TBD


Arguments
---------

TBD

Reference Files
---------------

TBD