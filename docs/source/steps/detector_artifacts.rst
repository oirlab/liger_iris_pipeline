=========================
Remove Detector Artifacts
=========================

Description
-----------

TBD.


Algorithm
---------

The detector will have two types of artifacts; permanent/semi-permanent and transient artifacts. Dead pixels, hot pixels or “frozen” pixel fall with the permanent/semi-permanent artifacts while cosmic rays (CR) are within the transient artifacts. Dead pixel are pixels that no longer function. Hot pixels are sensitive pixels that can have a non-linear response to incoming photons. They can also turn on and off and can even respond normally until a certain flux is achieved in which they become non-linear. “Frozen” pixels are pixels that have a low response rate (opposite of the hot pixels), with similar types of problems. CRs are high energy photons from the sky that can hit the detector randomly and leave bright artifacts.

For all types of detector artifacts, they are generally difficult to remove or remove completely with flat-fielding. To deal with detector artifacts, they need to be either masked out or subtracted off. For permanent artifacts, a bad pixel mask is used to mask the frame. Bad pixel masks need to be throughout the lifetime of the detector. Over time more pixels may become dead, hot or frozen. In some cases, hot or frozen pixels might be able to be recovered, depending on their severity. Hot, dead or frozen pixels, can be found by taking various length N number of dark exposures and median combining them, if features are 10-20 sigma above and below the noise level, they will be clippedadded to the masked. Since the pixel-to-pixel response will change, we may apply a set of flat-fielding before clipping. CRs on the other hand need to be removed from the frame. There are several methods for removing CRs such as L.A. Cosmic (Dokkem et al. 2001) which takes the Laplacian to find artifacts with steep slopes in individual frames. In the most severe cases it is possible find cosmic rays by taking a median of several science and calibration frames. In order to properly mitigate CRs in the median case, one needs 3 or more frames in multiples of odd numbers (i.e. 3, 5, 7…).


Subarrays
---------

TBD


Arguments
---------

TBD

Reference Files
---------------

TBD