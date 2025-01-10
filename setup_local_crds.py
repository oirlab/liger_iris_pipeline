# Setup the local CRDS cache for iris_pipeline
# This script can be executed at the beginning of Jupyter Notebooks
# with `%run`.
from pathlib import Path
HOME = str(Path.home())
import os
os.environ["CRDS_PATH"]=HOME + "/crds_cache"
os.environ["CRDS_CONTEXT"]="ligeriri_0001.pmap"
os.environ["CRDS_SERVER_URL"]="https://crds-serverless-mode.stsci.edu"
os.environ["CRDS_INI_FILE"]=HOME + "/crds_cache/crds.ini"
os.environ["CRDS_ALLOW_BAD_PARKEY_VALUES"]="1"
