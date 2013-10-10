#!/usr/bin/env bash
set -e

#####################################################
#
# download_python_pkgs.sh
#
# Use download .egg packages from an S3 bucket 
#
# Usage:
#
#    download_python_pkgs.sh S3_URL SAVE_DIR
# 
# where `S3_URL` is the URL of an S3 bucket
# containing .egg files
#
# and `SAVE_DIR` is the directory in which to save 
# the .egg files.
#
######################################################

if [ $# -ne 2 ]; then
    echo "Usage: $0 S3_URL SAVE_DIR"
    exit 1
fi

S3_URL=$1
SAVE_DIR=$2

# Create the save directory if it doesn't already exist
mkdir -p $SAVE_DIR

# Retrieve the list of files in the bucket
echo "Downloading Python packages from S3..."
curl $S3_URL | xml_grep 'Key' --text_only > $SAVE_DIR/python_pkgs.txt

# Install each package into the virtualenv
# If an error occurs, print stderr but do not abort
echo "Installing Python packages..."
while read package; do
    curl $S3_URL/$package > $SAVE_DIR/$package || echo "Could not download $package"
done < $SAVE_DIR/python_pkgs.txt
