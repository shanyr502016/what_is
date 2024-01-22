#!/bin/bash

# This is the launcher script for sbautomation on linux
SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
SCRIPTPATH=$(dirname "$SCRIPT")
PYTHON_HOME=/usr/bin/python3
PYTHON_BIN=python
export ENVIRONMENT_NAME=BUILD; export ENVIRONMENT_NAME
if [[ -z "${SMO_SHARE_LNX_ROOT}" ]]; then
    echo "Please set the SMO_SHARE_LNX_ROOT"
elif [[ -z "${SMO_SHARE_WIN_ROOT}" ]]; then
    echo "Please set the SMO_SHARE_WIN_ROOT"
elif [[ -z "${SMO_PACKAGE_SHARE}" ]]; then
    echo "Please set the SMO_PACKAGE_SHARE"
elif [[ -z "${DITA_LOG_LOCATION}" ]]; then
    echo "Please set the DITA_LOG_LOCATION"
else    
    # $PYTHON_HOME $SCRIPTPATH/deployment.py "$@"
    # echo $?
    set +e
	source "/smo_share/tcdownload/python-portable/virtualenv-3.6.15/bin/activate"
	python -u $SCRIPTPATH/tcbuild.py "$@"
    echo $?
fi





