#!/usr/bin/env bash
set -e

#####################################################
#
# python_pkgs.sh
#
# Use easy_install to download packages from
# an S3 bucket and install them in the system.
#
# Usage:
#
#    python_pkgs.sh S3_URL
# 
# where `S3_URL` is the URL of an S3 bucket
# containing .egg files
#
######################################################

if [ $# -ne 1 ]; then
    echo "Usage: $0 S3_URL"
    exit 1
fi

S3_URL=$1

# Retrieve the list of files in the bucket
echo "Downloading Python packages from S3..."
curl $S3_URL | xml_grep 'Key' --text_only > /tmp/python_pkgs.txt

# Install each package into the virtualenv
# If an error occurs, print stderr but do not abort
echo "Installing Python packages..."
while read package; do
    easy_install $S3_URL/$package || true
done < /tmp/python_pkgs.txt
