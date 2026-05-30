from .. import datamodels
import numpy as np
from stcal.jump.jump import detect_jumps_data
from stcal.jump.jump_class import JumpData

__all__ = ['jump_detection_jwst']

def jump_detection_jwst(
    ramp_data: np.ndarray,
    dq_raw: np.ndarray,
    dq: np.ndarray,
    gain: np.ndarray | None = None,
    rdnoise: np.ndarray | None = None,
    max_cores: int = 1,
    rejection_threshold: float = 4.0
):
    n_reads, ny, nx = ramp_data.shape

    if rdnoise is None:
        rdnoise = np.zeros((ny, nx), dtype=np.float32)
    if gain is None:
        gain = np.ones((ny, nx), dtype=np.float32)

    assert n_reads >= 2, "Need at least 2 reads to do jump detection."

    jump_data = JumpData()
    # Add the first axis for integrations (nints=1)
    jump_data.data = ramp_data[np.newaxis, :, :, :]
    jump_data.gdq = dq_raw[np.newaxis, :, :, :]
    jump_data.pdq = dq
    jump_data.gain_2d = gain
    jump_data.rnoise_2d = rdnoise
    jump_data.rejection_thresh = rejection_threshold
    jump_data.three_grp_thresh = rejection_threshold
    jump_data.four_grp_thresh = rejection_threshold
    jump_data.flag_4_neighbors = False
    jump_data.expand_large_events = False
    jump_data.minimum_sigclip_groups = np.inf
    jump_data.min_sat_area = 0
    jump_data.expand_factor = 0.0
    jump_data.sat_required_snowball = False
    jump_data.min_sat_radius_extend = 0.0
    jump_data.sat_expand = 0
    jump_data.edge_size = 0
    jump_data.find_showers = False
    jump_data.min_diffs_single_pass = 0
    jump_data.max_extended_width = np.inf
    jump_data.minimum_groups = 3
    jump_data.only_use_ints = False
    jump_data.grps_masked_after_shower = 0
    jump_data.mask_persist_grps_next_int = False
    jump_data.persist_grps_flagged = 0

    # Let stcal handle parallelization internally
    jump_data.max_cores = str(max_cores)

    jump_data.fl_good = datamodels.DQ_FLAGS['GOOD']
    jump_data.fl_sat = datamodels.DQ_FLAGS['SATURATED']
    jump_data.fl_jump = datamodels.DQ_FLAGS['JUMP_DET']
    jump_data.fl_ngv = datamodels.DQ_FLAGS['UNRELIABLE_FLAT']
    jump_data.fl_dnu = datamodels.DQ_FLAGS['DO_NOT_USE']
    jump_data.fl_ref = datamodels.DQ_FLAGS['REFERENCE_PIXEL']

    gdq, pdq, _, _ = detect_jumps_data(jump_data)
    # Drop the first axis to match your original 3D dq shape
    gdq = gdq[0].astype(np.uint32)

    return gdq, pdq