from ..stpipe.base_step import LigerIRISStep
from .. import datamodels
from .fit_ramp_numba import fit_ramps_ols, fit_ramps_mcds, fit_ramps_single
from .fit_ramp_jwst import fit_ramps_jwst
from ..calibrations import GainSelector, ReadNoiseSelector

import numpy as np

import logging

logger = logging.getLogger(__name__)

__all__ = ["RampFitStep"]


class RampFitStep(LigerIRISStep):
    """
    Fit or sample the up the ramp data to produce a 2D rate map.

    Parameters
    ----------
    input : RampModel
        Input ramp model to fit.
    method : str
        Ramp fitting method. Options are 'ols', 'cds', 'mcds', 'single', 'jwst_likely', 'jwst_fixsen', and 'cython_likely'. Default is 'cython_likely'.
    mcds_num_coadd : int
        The number of coadds for the 'mcds' method. Default is 3. Ignored for other methods.
    single_read_num : int
        Index of the read to use for the 'single' method. Supports negative indexing (-1 = last read). Default is -1. Ignored for other methods.
    jwst_jump_detection : bool
        Whether to perform jump detection as in JWST pipeline. Only for 'jwst_likely' and 'jwst_fixsen' methods. Default is False.
    jwst_jump_rejection_threshold : float
        Rejection threshold for jump detection if enabled. Default is 4.0.
    max_cores : int, optional
        Maximum number of CPU cores to use.
        Default is 1.

    Calibrations
    ------------
    gain : GainModel
    rn : ReadNoiseModel
    
    Returns
    -------
    ImagerModel or IFSImageModel
        The fitted ramp as a 2D rate map.
    """

    spec = """
        method = string(default='cython_likely')  # Ramp fit method. Options are 'ols', 'cds', 'mcds', 'single', 'jwst_likely', 'jwst_fixsen', 'cython_likely'.
        mcds_num_coadd = integer(default=3) # The number of coadds for the 'mcds' method.
        single_read_num = integer(default=-1) # Read index for the 'single' method. Supports negative indexing.
        jwst_jump_detection = boolean(default=False) # Whether to perform jump detection as in JWST pipeline
        jwst_jump_rejection_threshold = float(default=4.0) # Rejection threshold for jump detection if enabled
    """

    calibrations = {
        'gain' : {
            'selector' : GainSelector,
            'selector_kwargs' : {}
        },
        'rn' : {
            'selector' : ReadNoiseSelector,
            'selector_kwargs' : {}
        }
    }
    class_alias = "ramp_fit"

    def process(self, input : datamodels.RampModel):

        # Open the input data model
        input_model = self.open_model(input)

        # Get output model
        if not isinstance(input_model, datamodels.ProcessedRampModel):
            input_model = datamodels.ProcessedRampModel.from_datamodels(
                input_model,
                include_data=True
            )

        # Check the jump detection and ramp fitting method compatibility
        if self.jwst_jump_detection and self.method.lower() not in ('jwst_likely', 'jwst_ols'):
            raise ValueError(
                "JWST jump detection is only for shared memory optimization in combination with JWST ramp fitting methods."
                "Please set jwst_jump_detection to False or change ramp fitting algorithm."
            )

        logger.info(f"Fitting ramp with method={self.method.lower()}")

        # Get the gain and read noise reference files
        gain_ref, _ = self.get_calibration(input_model, "gain")
        logger.info(f"Using gain reference {gain_ref}")

        rn_ref, _ = self.get_calibration(input_model, "rn")
        logger.info(f"Using read noise reference {rn_ref}")

        _mcds_num_coadd = self.mcds_num_coadd

        # Get the read time info
        delta_readtimes = input_model.get_delta_readtimes()
        first_read_mjd = input_model.get_first_read_mjd()

        # Opwn the calibration files and fit the ramps
        with self.open_model(gain_ref) as gain_model, \
             self.open_model(rn_ref) as rn_model:

            # Fit the ramps
            if self.method.lower() == 'ols':
                result = fit_ramps_ols(
                    delta_readtimes,
                    input_model.data,
                    dq_raw=input_model.dq_raw,
                    dq=input_model.dq,
                    rdnoise=rn_model.rn,
                    gain=gain_model.gain,
                    start_times=first_read_mjd,
                    max_cores=self.max_cores
                )
            elif self.method.lower() == 'cds':
                result = fit_ramps_mcds(
                    delta_readtimes,
                    input_model.data,
                    dq_raw=input_model.dq_raw,
                    dq=input_model.dq,
                    rdnoise=rn_model.rn,
                    gain=gain_model.gain,
                    start_times=first_read_mjd,
                    num_coadd=1,
                    max_cores=self.max_cores
                )
            elif self.method.lower() == 'mcds':
                if _mcds_num_coadd is None:
                    n_read = input_model.data.shape[0]
                    _mcds_num_coadd = np.max([n_read // 4, 1]) # Ensure at least 1 read is used.
                result = fit_ramps_mcds(
                    delta_readtimes,
                    input_model.data,
                    dq_raw=input_model.dq_raw,
                    dq=input_model.dq,
                    rdnoise=rn_model.rn,
                    gain=gain_model.gain,
                    start_times=first_read_mjd,
                    num_coadd=_mcds_num_coadd,
                    max_cores=self.max_cores
                )
            elif self.method.lower() == 'single':
                result = fit_ramps_single(
                    delta_readtimes,
                    input_model.data,
                    dq_raw=input_model.dq_raw,
                    dq=input_model.dq,
                    rdnoise=rn_model.rn,
                    gain=gain_model.gain,
                    start_times=first_read_mjd,
                    read_num=self.single_read_num,
                )
            elif self.method.lower() in ('jwst_likely', 'jwst_fixsen', 'cython_likely'):
                result = fit_ramps_jwst(
                    delta_readtimes, input_model.data,
                    dq_raw=input_model.dq_raw,
                    dq=input_model.dq,
                    rdnoise=rn_model.rn,
                    gain=gain_model.gain,
                    start_times=first_read_mjd,
                    max_cores=self.max_cores,
                    algorithm=self.method.lower(),
                    jump_detection = self.jwst_jump_detection,
                    jump_rejection_threshold = self.jwst_jump_rejection_threshold
                )
            else:
                logger.error(f"Invalid ramp fit method {self.method.lower()}")
                raise ValueError(f"Invalid ramp fit method {self.method.lower()}")

        # Construct output model
        if input_model.meta.instrument.mode.lower() == 'img':
            output_model_class = datamodels.ImagerModel
        elif input_model.meta.instrument.mode.lower() == 'ifs':
            output_model_class = datamodels.IFSImageModel
        else:
            logger.error(f"Unsupported instrument mode {input_model.meta.instrument.mode} for ramp fitting output.")
            raise ValueError(f"Unsupported instrument mode {input_model.meta.instrument.mode} for ramp fitting output.")
        
        output_model = output_model_class.from_datamodels(
            input_model,
            data=result['rate'],
            err=result['rate_err'],
            var_rnoise=result['rate_var_rnoise'],
            var_poisson=result['rate_var_poisson'],
            dq=result['dq'],
            meta={'data_level': '1'}
        )

        return output_model