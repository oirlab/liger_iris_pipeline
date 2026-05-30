from ..stpipe.base_step import LigerIRISStep
from .. import datamodels
import numpy as np

from . import reference_SCALES_DRP as scales_drp

import logging
logger = logging.getLogger(__name__)

__all__ = ['RefPixelCorrectionStep']


class RefPixelCorrectionStep(LigerIRISStep):
    """
    This step subtracts the correlated read noise (i.e., 1/f noise) using reference pixels.
    Reference pixels are insensitive to light, but they track drifts in the readout electronics.

    For now: This step applies reference pixel correction to the input data
    using the SCALES-DRP algorithm (Author: Athira Unni).
    https://github.com/scalessim/SCALES-DRP/blob/main/scalesdrp/primitives/reference.py

    todo: Eventually for HISPEC, the goal is to use 4 reference pixels on each edge of the detector as well as a 65th reference channel that is read concurrently with the 64 science channels.

    todo: explore best 1/f noise correction algorithm.
    We might even be able to optionally fit and subtract the 1/f noise during the spectral extraction step in stage 1.

    todo: eveluate benefits of implementing a IRS2 readout pattern for HISPEC, which has more reference pixels interleaved with science pixels.

    References:
    Roman Roman-STScI-000673: Application and Characterization of IRRC on Roman/WFI TVAC1 Data
    https://www.stsci.edu/files/live/sites/www/files/home/roman/documentation/technical-documentation/_documents/Roman-STScI-000673.pdf

    JWST:
    https://jwst-pipeline.readthedocs.io/en/stable/jwst/refpix/description.html

    Parameters
    ----------
    input : RampModel
        A RampModel to correct the reference pixels for.
    method : str, optional
        The reference pixel correction method to use. Currently, only
        ``'scales_drp'`` is supported. Default is ``'scales_drp'``.
    n_channels : int or None, optional
        Number of readout channels in the detector. If ``None``, the value is
        taken from the input model metadata. Default is ``None``.
    n_ref_left : int or None, optional
        Number of reference pixels on the left side of each channel. If
        ``None``, the value is taken from the input model metadata. Default is ``None``.
    n_ref_right : int or None, optional
        Number of reference pixels on the right side of each channel. If
        ``None``, the value is taken from the input model metadata. Default is ``None``.
    vertical : bool or None, optional
        Whether the readout channels are oriented vertically. If ``None``, the
        value is taken from the input model metadata. Default is ``None``.

    Returns
    -------
    output : RampModel
        Reference pixel-corrected data model.


    References
    ----------
    Unni, A., Sallum, S., Benac, P., Fitzgerald, M. P., et al., "SCALES-DRP : A Data Reduction Pipeline for an Upcoming Keck Thermal Infrared Spectrograph", arXiv, arXiv:2509.15489 (2025)
    https://ui.adsabs.harvard.edu/abs/2025arXiv250915489U/abstract
    """

    spec = """
        method = string(default='scales_drp') # The reference pixel correction method to use. Currently, only 'scales_drp' is supported.
        n_channels = integer(default=None) # Number of readout channels in the detector. If None, the value is taken from the input model metadata.
        n_ref_left = integer(default=None) # Number of reference pixels on the left side of each channel. If None, the value is taken from the input model metadata.
        n_ref_right = integer(default=None) # Number of reference pixels on the right side of each channel. If None, the value is taken from the input model metadata.
        vertical = boolean(default=None) # Whether the readout channels are oriented vertically. If None, the value is taken from the input model metadata.
    """

    class_alias = "refpix"

    def process(self, input):

        input_model = self.open_model(input)

        if self.n_channels is None:
            _n_channels =  input_model.meta.n_channels
        else:
            _n_channels = self.n_channels
        if self.vertical is None:
            _vertical = input_model.meta.instrument.channels_are_vertical
        else:
            _vertical = self.vertical
        if self.n_ref_left is None:
            _n_ref_left = input_model.meta.instrument.n_refpixs
        else:
            _n_ref_left = self.n_ref_left
        if self.n_ref_right is None:
            _n_ref_right = input_model.meta.instrument.n_refpixs
        else:
            _n_ref_right = self.n_ref_right

        logger.info(f"Applying reference pixel correction to {input_model}")

        if input_model.data.dtype != np.float32:
            logger.info(f"Converting UTR data from {input_model.data.dtype} to float32")
            input_model.__dict__['data'] = input_model.data.astype(np.float32)

        if not _vertical:
            _data = np.transpose(input_model.data, (0, 2, 1))
        else:
            _data = input_model.data

        if self.method.lower() == 'scales_drp':
            scales_drp.ref_filter(
                cube=_data,
                nchans=_n_channels,
                in_place=True,
                avg_type='frame',
                perint=False,
                edge_wrap=False,
                left_ref=True, right_ref=True,
                nleft=_n_ref_left, nright=_n_ref_right
            )
        else:
            raise ValueError(f"Unknown reference pixel correction method: {self.method}")

        if not _vertical:
            input_model.__dict__['data'] = np.transpose(_data, (0, 2, 1))
        else:
            input_model.__dict__['data'] = _data


        return input_model