#!/usr/bin/python

import argparse
import datetime
import logging
import math
import os
import shutil
import socket
import subprocess
import sys

import boto
import raven


def download_from_gcloud_storage(tracking_logs_dir, bucket):
    """
    Download a file from the specified Google Cloud Storage bucket.

    Note that the host machine must be properly configured to use boto with a
    Google Cloud Platform service account. See
    https://cloud.google.com/storage/docs/xml-api/gspythonlibrary.

    tracking_logs_dir: An absolute path to the dir where the files
                       should stored.
    bucket: The name of a Google Cloud Storage bucket.
    """

    import gcs_oauth2_boto_plugin

    gcloud_uri = boto.storage_uri(bucket, 'gs')
    for key in gcloud_uri.get_bucket():
    	if not os.path.exists(tracking_logs_dir + key.name):
    	    logging.info('Downloading tracking log "{}" from Google Cloud '
                         'Storage bucket "{}"'.format(key.name, bucket))
    	    tl_file = open(tracking_logs_dir + key.name, "w")
            key.get_contents_to_file(tl_file)
    	else:
    	    print key.name + ' already exists'
            logging.info('Tracking log "{}" alredy exists '.format(key.name))

    logging.info('Download successful')


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--provider', help='gs or s3')
    parser.add_argument('-b', '--bucket', help='bucket name')
    parser.add_argument('--sentry-dsn', help='Sentry data source name')

    return parser.parse_args()


def _main():
    args = _parse_args()

    program_name = os.path.basename(sys.argv[0])
    bucket = args.bucket or os.environ.get('TRACKING_LOGS_BUCKET')
    provider = args.provider or os.environ.get('TRACKING_LOGS_STORAGE_PROVIDER', 'gs')
    sentry_dsn = args.sentry_dsn or os.environ.get('TRACKING_LOGS_SENTRY_DSN', '')

    sentry = raven.Client(sentry_dsn)
    tracking_logs_dir = "/edx/var/log/tracking/"

    if provider == 'gs':
        download_from_gcloud_storage(tracking_logs_dir, bucket)

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    _main()
