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


def upload_to_gcloud_storage(file_path, bucket):
    """
    Upload a file to the specified Google Cloud Storage bucket.

    Note that the host machine must be properly configured to use boto with a
    Google Cloud Platform service account. See
    https://cloud.google.com/storage/docs/xml-api/gspythonlibrary.

        file_path: An absolute path to the file to be uploaded.
        bucket: The name of a Google Cloud Storage bucket.
    """

    import gcs_oauth2_boto_plugin

    logging.info('Uploading tracking logs at "{}" to Google Cloud Storage bucket '
                 '"{}"'.format(file_path, bucket))

    file_name = os.path.basename(file_path)
    gcloud_uri = boto.storage_uri(bucket + '/' + file_name, 'gs')
    gcloud_uri.new_key().set_contents_from_filename(file_path)
    logging.info('Upload successful')


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--provider', help='gs or s3')
    parser.add_argument('-b', '--bucket', help='bucket name')
    parser.add_argument('--sentry-dsn', help='Sentry data source name')

    return parser.parse_args()


def _main():
    args = _parse_args()

    bucket = args.bucket or os.environ.get('TRACKING_LOGS_BUCKET')
    provider = args.provider or os.environ.get('TRACKING_LOGS_STORAGE_PROVIDER', 'gs')
    sentry_dsn = args.sentry_dsn or os.environ.get('TRACKING_LOGS_SENTRY_DSN', '')

    sentry = raven.Client(sentry_dsn)
    tracking_logs_dir = "/edx/var/log/tracking/"

    for tl_filename in os.listdir(tracking_logs_dir):
        try:
            upload_to_gcloud_storage(tracking_logs_dir + tl_filename, bucket)
        except:
            logging.exception("The tracking logs copy has failed!")
            sentry.captureException()

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    _main()
