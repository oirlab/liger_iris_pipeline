======
Mosaic
======

Description
-----------

TBD.


Algorithm
---------

Imager: Mosaicking in the imager will be based on the dither pattern selected, and integer and non-integer pixel shifts will be supported. The dithers will be stored in the FITS header keywords and there will be support for an external file with the offsets. For integer pixel shits, frames will be combined using the median or mean, with sigma clipping to clip out deviant pixels. The clipping options will include using the standard deviation or median absolute deviation (MAD). For non-integer pixel shifts, there are widely used efficient software packages that handle drizzling and resampling, such as SWarp and DrizzlePac (previously known as AstroDrizzle).[j]

IFS: Mosaicking in the IFS will be relative to a source or the dither keywords in the FITS headers at a fixed PA. There will also be an option to stack the images based on an external offsets file. Currently, only integer pixel shifts will be supported. Frames will be combined using the median or mean, with sigma clipping to clip out deviant pixels. The clipping options will include using the standard deviation or median absolute deviation (MAD).


Subarrays
---------

TBD


Arguments
---------

TBD

Reference Files
---------------

TBD