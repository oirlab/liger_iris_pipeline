import logging
from ..datamodels import LigerFlatModel, LigerDarkModel, LigerImagerModel

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def get_subarray_model(sci_model, ref_model):

    """
    Create a subarray version of a reference file model that matches
    the subarray characteristics of a science data model. A new
    model is created that contains subarrays of all data arrays
    contained in the reference file model.

    Parameters
    ----------
    sci_model: JWST data model
        science data model

    ref_model: JWST data model
        reference file data model

    Returns
    -------
    sub_model: JWST data model
        subarray version of the reference file model
    """

    if sci_model.meta.subarray.name != "FULL":

        # Get the science model subarray params
        xstart_sci = sci_model.meta.subarray.xstart
        xsize_sci = sci_model.meta.subarray.xsize
        ystart_sci = sci_model.meta.subarray.ystart
        ysize_sci = sci_model.meta.subarray.ysize

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
            "slice xstart=%d, xstop=%d, ystart=%d, ystop=%d", xstart, xstop, ystart, ystop
        )

        # Make sure that the slice limits are within the bounds of
        # the reference file data array
        if (
            xstart < 0
            or ystart < 0
            or xstop > xsize_ref
            or ystop > ysize_ref
        ):
            log.error(
                "Computed reference file slice indexes are incompatible with size of reference data array"
            )
            log.error(
                "Science: SUBSTRT1=%d, SUBSTRT2=%d, SUBSIZE1=%d, SUBSIZE2=%d",
                xstart_sci,
                ystart_sci,
                xsize_sci,
                ysize_sci,
            )
            log.error(
                "Reference: SUBSTRT1=%d, SUBSTRT2=%d, SUBSIZE1=%d, SUBSIZE2=%d",
                xstart_ref,
                ystart_ref,
                xsize_ref,
                ysize_ref,
            )
            log.error(
                "Slice indexes: xstart=%d, xstop=%d, ystart=%d, ystop=%d",
                xstart,
                xstop,
                ystart,
                ystop,
            )
            raise ValueError("Bad reference file slice indexes")

        # Extract subarrays from each data attribute in the particular
        # type of reference file model and return a new copy of the
        # data model
        if isinstance(ref_model, FlatModel):
            sub_data = ref_model.data[ystart:ystop, xstart:xstop]
            sub_err = ref_model.err[ystart:ystop, xstart:xstop]
            sub_dq = ref_model.dq[ystart:ystop, xstart:xstop]
            sub_model = FlatModel(data=sub_data, err=sub_err, dq=sub_dq)
            sub_model.update(ref_model)
        elif isinstance(ref_model, DarkModel):
            sub_data = ref_model.data[ystart:ystop, xstart:xstop]
            sub_err = ref_model.err[ystart:ystop, xstart:xstop]
            sub_dq = ref_model.dq[ystart:ystop, xstart:xstop]
            sub_model = DarkModel(data=sub_data, err=sub_err, dq=sub_dq)
            sub_model.update(ref_model)
        elif isinstance(ref_model, LigerIrisImageModel):
            sub_data = ref_model.data[ystart:ystop, xstart:xstop]
            sub_err = ref_model.err[ystart:ystop, xstart:xstop]
            sub_dq = ref_model.dq[ystart:ystop, xstart:xstop]
            sub_model = LigerIrisImageModel(data=sub_data, err=sub_err, dq=sub_dq)
            sub_model.update(ref_model)
        else:
            log.warning("Unsupported reference file model type")
            sub_model = None

        return sub_model
    else:
        return ref_model
