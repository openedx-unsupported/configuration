#!/usr/bin/env bash
set -e

#####################################################
#
# install_python_pkgs.sh
#
# Use easy_install to install all
# .egg files in a folder into a virtualenv.
#
# Usage:
#
#    install_python_pkgs.sh EGG_DIR VENV
# 
# where `EGG_DIR` is the directory containing
# the .egg files
#
# and `VENV` is the virtualenv in which to install
# the packages.  If the virtualenv does not yet
# exist, it will be created.
#
# If the virtualenv already exists, it will not
# be modified.
#
######################################################

if [ $# -ne 2 ]; then
    echo "Usage: $0 EGG_DIR VENV"
    exit 1
fi

EGG_DIR=$1
VENV=$2

if [ -e $VENV/bin/activate ]; then
    echo "$VENV already exists; skipping installation..."
else

    # Create python egg cache and set correct permissions
    PYTHON_EGG_CACHE=$HOME/.python-eggs
    mkdir -p $PYTHON_EGG_CACHE
    chmod 600 $PYTHON_EGG_CACHE

    # Create and activate the virtualenv
    echo "No virtualenv found; creating it..."
    mkdir -p $VENV
    virtualenv $VENV
    . $VENV/bin/activate

    # Install the .egg files into the virtualenv
    echo "Installing Python eggs..."
    for egg_file in $EGG_DIR/*.egg; do
        easy_install $egg_file || true
    done
fi
