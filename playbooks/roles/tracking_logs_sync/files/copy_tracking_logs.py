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


def upload_to_gcloud_storage(file_path, bucket, multiple_edxapp_vm):
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

    if multiple_edxapp_vm and multiple_edxapp_vm == "yes":
        file_name = '%s-%s%s' % (file_name[:-3], socket.gethostname(), file_name[-3:])

    gcloud_uri = boto.storage_uri(bucket + '/' + file_name, 'gs')
    gcloud_uri.new_key().set_contents_from_filename(file_path)
    logging.info('Upload successful')


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--provider', help='gs or s3')
    parser.add_argument('-b', '--bucket', help='bucket name')
    parser.add_argument('--sentry-dsn', help='Sentry data source name')
    parser.add_argument('--multiple-edxapp-vm', help='Multiple edxapp vm')

    return parser.parse_args()


def _main():
    args = _parse_args()

    bucket = args.bucket or os.environ.get('TRACKING_LOGS_BUCKET')
    provider = args.provider or os.environ.get('TRACKING_LOGS_STORAGE_PROVIDER', 'gs')
    sentry_dsn = args.sentry_dsn or os.environ.get('TRACKING_LOGS_SENTRY_DSN', '')
    multiple_edxapp_vm = args.multiple_edxapp_vm or os.environ.get('TRACKING_LOGS_MULTIPLE_EDXAPP_VM', False)

    sentry = raven.Client(sentry_dsn)
    tracking_logs_dir = "/edx/var/log/tracking/"

    for tl_filename in os.listdir(tracking_logs_dir):
        try:
            upload_to_gcloud_storage(tracking_logs_dir + tl_filename, bucket, multiple_edxapp_vm)
        except:
            logging.exception("The tracking logs copy has failed!")
            sentry.captureException()

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    _main()
