import os
from astropy.utils import data
import warnings

PREDEFINED_DATA_FOLDERS=["data/"]
#DATAURL="https://tmt-test-data.s3-us-west-1.amazonaws.com/iris_pipeline/"
DATAURL="https://ndownloader.figshare.com/files/"

def get_data_from_url(filename):
    """Retrieves input templates from remote server,
    in case data is available in one of the PREDEFINED_DATA_FOLDERS defined above,
    e.g. at NERSC, those are directly returned."""

    for folder in PREDEFINED_DATA_FOLDERS:
        full_path = os.path.join(folder, filename)
        if os.path.exists(full_path):
            warnings.warn(f"Access data from {full_path}")
            return full_path
    with data.conf.set_temp("dataurl", DATAURL), data.conf.set_temp(
        "remote_timeout", 30
    ):
        warnings.warn(f"Retrieve data for {filename} (if not cached already)")
        local_path = data.get_pkg_data_filename(filename, show_progress=True)
        local_path_suffix = local_path + ".fits"
        if not os.path.exists(local_path_suffix):
            os.symlink(local_path, local_path_suffix)
    return local_path_suffix
