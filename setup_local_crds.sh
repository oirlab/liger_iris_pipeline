echo 'Make sure you run this script with'
echo '> source setup_local_crds.sh'
echo 'So that the variables are setup in the current session'
export CRDS_PATH="$HOME/crds_cache"
export CRDS_CONTEXT="ligeriri_0001.pmap"
export CRDS_SERVER_URL="https://crds-serverless-mode.stsci.edu"
export CRDS_INI_FILE=$CRDS_PATH/crds.ini
export CRDS_ALLOW_BAD_PARKEY_VALUES=1