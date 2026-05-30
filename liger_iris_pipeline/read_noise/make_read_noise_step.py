from ..stpipe.base_step import LigerIRISStep
from .. import datamodels
import numpy as np
from typing import Sequence
from ..datamodels.dqflags import DQ_FLAGS
from ..gain.make_gain_step import fit_gain_and_readnoise
from ..calibrations import GainSelector, ReadNoiseSelector

import numbers
import logging
logger = logging.getLogger(__name__)

__all__ = ['MakeReadNoiseStep']

SATURATED_FLAG_uint8 =  np.uint8(DQ_FLAGS["SATURATED"])
DO_NOT_USE_FLAG_uint8 = np.uint8(DQ_FLAGS["DO_NOT_USE"])
JUMP_DET_FLAG_uint8 = np.uint8(DQ_FLAGS["JUMP_DET"])

class MakeReadNoiseStep(LigerIRISStep):
    """
    Estimate detector read noise from up-the-ramp data.

    This step fits the detector read noise parameter from raw
    **dark** up-the-ramp (UTR) ramps using the maximum-likelihood framework
    described by Time Brandt (2025; PASP, 137, 125006).
    
    In this case, the gain is fixed and only the read-noise is fitted.
    
    Three fitting strategies are supported (see ``method`` argument):

    1. A grid-based maximum-likelihood search that evaluates the likelihood on a grid of read noise values defined by the user (e.g., using the ``init_RN`` and ``init_delta_RNs`` parameters).

    2. A local quadratic approximation around an initial read noise value (e.g., defined by the ``init_RN`` parameter and a step size defined by the ``quad_delta_RN`` parameter).

    3. A hybrid approach that first performs a grid search to locate the optimum and then refines the solution with a quadratic approximation.

    An initial read-noise value may be provided explicitly (e.g., as an
    array defining a search grid). If not provided, the step is
    expected to obtain an appropriate default from the calibration database.
    An optional argument allows treating all ramps for a given pixel as having identical count
    rates.

    The fitting may be performed on a per-pixel basis or using a single
    model for the full detector. Although the full detector mode is only for
    testing.


    Parameters
    ----------
    input : list of str or list of RampModel
        List of input file paths or ramp models to process. Use dark exposures.
    init_RN : None or array-like, optional
        Initial read noise value(s) used to define the maximum-likelihood
        grid search. If None, obtain an initial value from the calibration
        database. If provided, this may be a scalar or an array defining the
        read-noise sampling (e.g., ``np.linspace(1, 20, 101)``).
    mode : {'per_pixel', 'channel', 'full_detector'}, optional
        Mode used to fit the parameters. ``'per_pixel'`` fits an independent
        read noise for each pixel. ``'full_detector'`` fits a single read
        noise value for the detector. ``'channel'`` is reserved for future
        implementation.
    method : {'grid', 'quad', 'both'}, optional
        Fitting strategy. Default is ``both``.
            
            - ``'grid'`` performs a maximum-likelihood grid search.
            - ``'quad'`` uses a quadratic approximation around the initial parameter.
            - ``'both'`` runs a grid search first and then refines the solution with a quadratic approximation.

    init_delta_RNs : array-like or None, optional
        Read-noise grid offsets used for the maximum-likelihood grid search.
        The read-noise sampling is defined as ``init_RN + init_delta_RNs``.
    quad_delta_RN : float, optional
        Only used when ``method='quad'``.
        Defines the initial read-noise step size around ``init_RN`` for the quadratic approximation.
        Default is 0.5.
    static_gain : float, optional
        Static gain value to use if no gain calibration is provided. If None, the gain will be obtained from the calibration database.
        Default is None.
    countratesidentical : bool, optional
        If True, assume all ramps have identical count rates.
        Default is False.
    max_cores : int, optional
        Maximum number of CPU cores to use.
        Default is 1.

    Returns
    -------
    output : DataModel
        Data model containing the fitted read noise parameter and associated
        fit diagnostics.

    References
    ----------
    Brandt, T. D. (2025), *Computing the Electronic Gain for Detectors Read
    Out Up-the-ramp*, PASP, 137, 125006.
    https://ui.adsabs.harvard.edu/abs/2025PASP..137l5006B/abstract

    Roman calibration pipeline reference:
    https://github.com/spacetelescope/romancal
    """

    spec = """
        init_RN = is_string_or_datamodel(default=None)  # Initial read noise value used to define the maximum-likelihood grid search.
        max_cores = integer(default=1)  # Maximum number of CPU cores to use for parallel processing.
        mode = string(default='per_pixel')  # Mode used to fit the parameters. 'per_pixel', 'full_detector', or 'per_channel' (under consideration).
        method = string(default='both')  # Fitting strategy. 'quad', 'grid', or 'both'.
        init_delta_RN_start = float(default=-10)  # Initial value for the read-noise grid search.
        init_delta_RN_step = float(default=0.2)  # Step size for the read-noise grid search.
        init_delta_RN_stop = float(default=10)  # Final value for the read-noise grid search.
        quad_delta_RN = float(default=0.5)  # Used only when method='quad'. Defines the initial read-noise step size around init_RN for the quadratic approximation.
        static_gain = float(default=None)  # Static gain value to use if no gain calibration is provided.
        countratesidentical = boolean(default=False)  # If True, assume all ramps have identical count rates.
        suffix = string(default='')
    """

    # init_delta_RN_range = list(default=[-10, 10])  # Range for the read-noise grid search.
    calibrations = {
        'gain' : {
            'selector' : GainSelector,
            'selector_kwargs' : {}
        },
        'rn_init' : {
            'selector' : ReadNoiseSelector,
            'selector_kwargs' : {}
        }
    }

    class_alias = "make_rn"

    def process(self, input):
        if self.mode.lower() != 'full_detector' and self.mode.lower() != 'per_pixel':
            raise NotImplementedError(
                f"Only 'full_detector' and 'per_pixel' modes are implemented currently. Not {self.mode}"
            )

        if isinstance(input, (datamodels.LigerIRISDataModel, str)):
            _input_list_tmp = [input]
        if isinstance(input, Sequence):
            _input_list_tmp = input
        logger.info(f"Deriving the detector readnoise from a list of {len(_input_list_tmp)} inputs.")

        input_models = [datamodels.open(f) for f in _input_list_tmp]
        datamodel0 = input_models[0]
        n_reads, ny, nx = datamodel0.data.shape

        if self.static_gain is None:
            gain, _ = self.get_calibration(datamodel0, 'gain')
            gain_model = datamodels.open(gain)
            gain_arr = gain_model.gain
        else:
            gain_arr = np.full((ny, nx), self.static_gain, dtype=np.float32)

        if self.init_RN is None:
            rn_cal_init, _ = self.get_calibration(datamodel0, 'rn_init')
            rn_model_init = datamodels.open(rn_cal_init)
            _init_center_RN = rn_model_init.rn
            logger.info(f"Using {rn_cal_init} as initial read noise values with median value {np.nanmedian(_init_center_RN)} DN.")
        elif isinstance(self.init_RN, numbers.Number):
            _init_center_RN = self.init_RN
            logger.info(f"Using user-defined initial read noise value: {self.init_RN} DN.")
        elif isinstance(self.init_RN, np.ndarray):
            _init_center_RN = self.init_RN
            logger.info(f"Using user-defined initial read noise values with median read noise: {np.nanmedian(_init_center_RN)} DN.")
        elif isinstance(self.init_RN, (str, datamodels.ReadNoiseModel)):
            rn_model = self.open_model(self.init_RN)
            _init_center_RN = rn_model.rn
            logger.info(f"Using user-defined initial read noise values with median read noise: {np.nanmedian(_init_center_RN)} DN.")

        delta_readtimes = datamodel0.get_delta_readtimes()

        if self.method == 'quad':
            _init_delta_RNs = np.array([-self.quad_delta_RN,0,+self.quad_delta_RN])
        elif self.method == 'grid' or self.method == 'both':
            _init_delta_RNs = np.arange(
                self.init_delta_RN_start,
                self.init_delta_RN_stop + self.init_delta_RN_step,
                self.init_delta_RN_step
            )
        
        if self.mode.lower() == 'full_detector':
            logger.info(
                "Running in full_detector mode. "
                "All detector pixels will be fitted jointly and a single gain and/or readnoise value will be returned for the entire chip."
            )
        elif self.mode.lower() == 'per_pixel':
            logger.info(
                "Running in single_pixel mode. "
                "Each detector pixel will be fitted independently and a map of gain and/or readnoise will be returned."
            )

        # Make all ramps from all files into a big cube
        n_files = len(input_models)
        ramp_arr = []
        dq_raw_arr = []
        for input_model in input_models:
            if n_reads != input_model.data.shape[0]:
                raise ValueError("All input ramps must have the same number of reads.")
            ramp_arr.append(input_model.data)
            dq_raw_arr.append(input_model.dq_raw)
        ramp_arr = np.array(ramp_arr)
        dq_raw_arr = np.array(dq_raw_arr)

        _out = fit_gain_and_readnoise(
            delta_readtimes, ramp_arr, dq_raw_arr, gain_arr, _init_center_RN,
            None, _init_delta_RNs,
            countratesidentical=self.countratesidentical,
            mode=self.mode, method=self.method, max_cores=self.max_cores
        )
        _, bestfit_rn, cov = _out

        if self.mode.lower() == 'full_detector':
            logger.info(f"Best-fit read noise: {bestfit_rn:.3f} e-")
        elif self.mode.lower() == 'per_pixel':
            logger.info(f"Best-fit read noise map with median value {np.nanmedian(bestfit_rn):.3f} e- and stddev {np.nanstd(np.abs(bestfit_rn - np.nanmedian(bestfit_rn))):.3f} e-.")

        # Get output read noise model
        output_read_noise = datamodels.ReadNoiseModel.from_datamodels(input_models)

        if self.mode.lower() == 'full_detector':
            output_read_noise.rn = np.full((ny, nx), bestfit_rn)
            output_read_noise.rn_err = np.full((ny, nx), np.sqrt(cov[1, 1]))
        elif self.mode.lower() == 'per_pixel':
            output_read_noise.rn = bestfit_rn
            output_read_noise.rn_err = np.sqrt(cov[1, 1])

        output_read_noise.dq = np.copy(input_models[0].dq)

        return output_read_noise