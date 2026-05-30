import logging
from .. import datamodels

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def get_subarray_model(input_model : datamodels.LigerIRISDataModel, ref_model : datamodels.LigerIRISDataModel):
    """
    Create a subarray version of a reference file model that matches
    the subarray characteristics of a science data model. A new
    model is created that contains subarrays of all data arrays
    contained in the reference file model.

    Parameters
    ----------
    input_model: LigerIRISDataModel
        The input datamodel that might have subarray(s).

    ref_model: LigerIRISDataModel
        The full datamodel to get the subarray frame for.

    Returns
    -------
    sub_model: LigerIRISDataModel
        subarray version of the reference file model
    """

    # This is the easiest solution for now to ignore Liger models
    if input_model.meta.instrument.name != 'IRIS' or input_model.meta.instrument.mode != 'IMG': # Or detector
        return ref_model
    
    # Extract subarray if not full frame
    if input_model.meta.subarray.name != "FULL":

        # Get the science model subarray params
        xstart_sci = input_model.meta.subarray.xstart
        xsize_sci = input_model.meta.subarray.xsize
        ystart_sci = input_model.meta.subarray.ystart
        ysize_sci = input_model.meta.subarray.ysize

        # Get the reference model subarray params
        xstart_ref = ref_model.meta.subarray.xstart or 1
        ystart_ref = ref_model.meta.subarray.ystart or 1
        xsize_ref = ref_model.meta.subarray.xsize or ref_model.data.shape[1]
        ysize_ref = ref_model.meta.subarray.ysize or ref_model.data.shape[0]

        # Compute the slice indexes, in 0-indexed python frame
        xstart = xstart_sci - xstart_ref
        ystart = ystart_sci - ystart_ref
        xstop = xstart + xsize_sci
        ystop = ystart + ysize_sci
        log.debug(
            f"slice xstart={xstart}, xstop={xstop}, ystart={ystart}, ystop={ystop}"
        )

        # Make sure that the slice limits are within the bounds of
        # the reference file data array
        if (
            xstart < 0
            or ystart < 0
            or xstop > xsize_ref
            or ystop > ysize_ref
        ):
            log.error("Computed reference file slice indexes are incompatible with size of reference data array")
            log.error(f"Science: SUBSTRT1={xstart_sci}, SUBSTRT2={ystart_sci}, SUBSIZE1={xsize_sci}, SUBSIZE2={ysize_sci}")
            log.error(f"Reference: SUBSTRT1={xstart_ref}, SUBSTRT2={ystart_ref}, SUBSIZE1={xsize_ref}, SUBSIZE2={ysize_ref}")
            log.error(f"Slice indexes: xstart={xstart}, xstop={xstop}, ystart={ystart}, ystop={ystop}")
            raise ValueError("Bad reference file slice indexes")

        # Extract subarrays from each data attribute in the particular
        # type of reference file model and return a new copy of the
        # data model
        # TODO: Consider automating this by detecting array dtypes with shape == ref_model.shape?
        ref_model_class = ref_model.__class__
        if isinstance(ref_model, (
            datamodels.DetectorFlatModel,
            datamodels.DarkModel,
            datamodels.ImagerModel,
        )):
            sub_data = ref_model.data[ystart:ystop, xstart:xstop]
            sub_err = ref_model.err[ystart:ystop, xstart:xstop]
            sub_dq = ref_model.dq[ystart:ystop, xstart:xstop]
            sub_model = ref_model_class(data=sub_data, err=sub_err, dq=sub_dq, meta=ref_model.meta)
        elif isinstance(ref_model, datamodels.DQModel):
            sub_dq = ref_model.dq[ystart:ystop, xstart:xstop]
            sub_model = ref_model_class(dq=sub_dq)
        elif isinstance(ref_model, datamodels.SaturationModel):
            sub_data = ref_model.sat_thresh[ystart:ystop, xstart:xstop]
            sub_dq = ref_model.dq[ystart:ystop, xstart:xstop]
            sub_model = ref_model_class(sat_thresh=sub_data, dq=sub_dq)
        else:
            log.warning("Unsupported file model type")
            sub_model = None

        return sub_model
    else:
        return ref_model
