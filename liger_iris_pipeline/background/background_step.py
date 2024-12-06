#! /usr/bin/env python


from .. import datamodels
from ..base_step import LigerIRISStep
from . import background_sub

__all__ = ["BackgroundStep"]


class BackgroundStep(LigerIRISStep):
    """
    BackgroundStep:  Subtract background exposures from target exposures.
    """

    spec = """
        sigma = float(default=3.0)  # Clipping threshold
        maxiters = integer(default=None)  # Number of clipping iterations
    """

    def process(self, input, bkg_list):

        """
        Subtract the background signal from target exposures by subtracting
        designated background images from them.

        Parameters
        ----------
        input: data model
            input target data model to which background subtraction is applied

        bkg_list: filename list
            list of background exposure file names

        Returns
        -------
        result: data model
            the background-subtracted target data model
        """

        # Load the input data model
        with datamodels.open(input) as input_model:

            # Do the background subtraction
            result = background_sub.background_sub(
                input_model, bkg_list, self.sigma, self.maxiters
            )
            result.meta.cal_step.back_sub = "COMPLETE"

        return result
