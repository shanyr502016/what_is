#!/bin/bash

# This is the launcher script for sbautomation on linux
SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
SCRIPTPATH=$(dirname "$SCRIPT")
PYTHON_HOME=/usr/bin/python3
PYTHON_BIN=python

if [[ -z "${ENVIRONMENT_NAME}" ]]; then
    echo "Please set the ENVIRONMENT NAME"
elif [[ -z "${SMO_SHARE_LNX_ROOT}" ]]; then
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
	python -u $SCRIPTPATH/deployment.py "$@"
    echo $?
fi





