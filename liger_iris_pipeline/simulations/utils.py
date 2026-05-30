import numpy as np

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from liger_iris_pipeline.datamodels import RampModel

def add_refchan_ramp(
    model : 'RampModel',
    channel_size : int = 64,
    value: float = 0,
):
    """
    Extend ramp data arrays to include ref channel on right side.
    
    Parameters
    ----------
    model : `RampModel`
        Input ramp data model.
    channel_size : int, optional
        Number of columns in each readout channel, by default 64.
    value : float, optional
        Constant value used to fill the reference channel, by default 0.
    """

    from liger_iris_pipeline.datamodels import DQ_FLAGS
    ref_flag = DQ_FLAGS['REFERENCE_PIXEL']

    # DATA ext
    pad_width = ((0, 0), (0, 0), (0, channel_size))
    model.data = np.pad(model.data, pad_width, mode="constant", constant_values=value)

    # DQ RAW ext
    if model._instance.get('dq_raw') is not None:
        model.dq_raw = np.pad(
            model.dq_raw,
            pad_width,
            mode="constant", constant_values=ref_flag
        )

        model.dq_raw[:, :4, :] = ref_flag
        model.dq_raw[:, -4:, :] = ref_flag
        model.dq_raw[:, :, :4] = ref_flag
        model.dq_raw[:, :, -4:] = ref_flag

    # DQ ext
    if model._instance.get('dq') is not None:
        pad_width = ((0, 0), (0, channel_size))
        model.dq = np.pad(
            model.dq,
            pad_width,
            mode="constant",
            constant_values=ref_flag
        )

        model.dq[:4, :] = ref_flag
        model.dq[-4:, :] = ref_flag
        model.dq[:, :4] = ref_flag
        model.dq[:, -4:] = ref_flag