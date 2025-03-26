Description
===========

Algorithm
---------

Simple normalization algorithms, it divides the input data by
their own median (default) or by using another `numpy` function
provided with the ``method`` argument, for example `mean`.

If ``method`` is "mode", it uses the ``scipy.stats.mode`` method.

It only considers the part of the data where the data quality array
is zero.

Currently it has only been tested with image frames.
