#!/usr/bin/python

import argparse
import datetime
import logging
import os
import shutil
import socket
import subprocess
import sys

import boto
import gcs_oauth2_boto_plugin


def make_file_name(base_name):
    """
    Create a file name based on the hostname, a base_name, and date
        e.g. openedxlite12345_mysql_20140102
    """

    hostname = socket.gethostname()
    return '{0}_{1}_{2}'.format(hostname, base_name, datetime.datetime.now().
                                strftime("%Y%m%d"))


def upload_to_s3(file_path, bucket, aws_access_key_id, aws_secret_access_key):
    """
    Upload a file to the specified S3 bucket.

        file_path: An absolute path to the file to be uploaded.
        bucket: The name of an S3 bucket.
        aws_access_key_id: An AWS access key.
        aws_secret_access_key: An AWS secret access key.
    """

    logging.info('Uploading backup at "{}" to Amazon S3 bucket "{}"'
                 .format(file_path, bucket))

    conn = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
    bucket = conn.lookup(bucket)
    file_name = os.path.basename(file_path)

    key = boto.s3.key.Key(bucket, file_name)
    key.set_contents_from_filename(file_path)
    logging.info('Upload successful')


def upload_to_gcloud_storage(file_path, bucket):
    """
    Upload a file to the specified Google Cloud Storage bucket.

    Note that the host machine must be properly configured to use boto with a
    Google Cloud Platform service account. See
    https://cloud.google.com/storage/docs/xml-api/gspythonlibrary.

        file_path: An absolute path to the file to be uploaded.
    """

    logging.info('Uploading backup at "{}" to Google Cloud Storage bucket '
                 '"{}"'.format(file_path, bucket))

    file_name = os.path.basename(file_path)
    gcloud_uri = boto.storage_uri(bucket + '/' + file_name, 'gs')
    gcloud_uri.new_key().set_contents_from_filename(file_path)
    logging.info('Upload successful')


def compress_backup(backup_path):
    """
    Compress a backup using tar and gzip.

        backup_path: An absolute path to a file or directory containing a
            database dump.

        returns: The absolute path to the compressed backup file.
    """

    logging.info('Compressing backup at "{}"'.format(backup_path))

    compressed_backup_path = backup_path + '.tar.gz'
    zip_cmd = ['tar', '-zcvf', compressed_backup_path, backup_path]

    ret = subprocess.call(zip_cmd, env={'GZIP': '-9'})
    if ret:  # if non-zero return
        error_msg = 'Error occurred while compressing backup'
        logging.error(error_msg)
        raise Exception(error_msg)

    return compressed_backup_path


def dump_service(service_name, backup_dir):
    """
    Dump the database contents for a service.

        service_name: The name of the service to dump, either mysql or mongodb.
        backup_dir: The directory where the database is to be dumped.

        returns: The absolute path of the file or directory containing the
            dump.
    """

    commands = {
        'mysql': 'mysqldump -u root --all-databases --single-transaction > {}',
        'mongodb': 'mongodump -o {}',
    }

    cmd_template = commands.get(service_name)
    if cmd_template:
        backup_filename = make_file_name(service_name)
        backup_path = os.path.join(backup_dir, backup_filename)
        cmd = cmd_template.format(backup_path)

        logging.info('Dumping database: `{}`'.format(cmd))
        ret = subprocess.call(cmd, shell=True)
        if ret:  # if non-zero return
            error_msg = 'Error occurred while dumping database'
            logging.error(error_msg)
            raise Exception(error_msg)

        return backup_path
    else:
        error_msg = 'Unknown service {}'.format(service_name)
        logging.error(error_msg)
        raise Exception(error_msg)


def clean_up(backup_path):
    """
    Remove the local database dump and the corresponding tar file if it exists.

        backup_path: An absolute path to a file or directory containing a
            database dump.
    """

    logging.info('Cleaning up "{}"'.format(backup_path))

    backup_tar = backup_path + '.tar.gz'
    if os.path.isfile(backup_tar):
        os.remove(backup_tar)

    if os.path.isdir(backup_path):
        shutil.rmtree(backup_path)
    elif os.path.isfile(backup_path):
        os.remove(backup_path)


def restore(service_name, backup_path, uncompress=True, settings=None):
    """
    Restore a database from a backup.

        service_name: The name of the service whose database is to be restored,
            either mysql or mongodb.
        backup_path: The absolute path to a backup.
        uncompress: If True, the backup is assumed to be a gzipped tar and is
            uncompressed before the database restoration.
    """

    if service_name == 'mongodb':
        restore_mongodb(backup_path, uncompress)
    elif service_name == 'mysql':
        restore_mysql(backup_path, uncompress, settings=settings)


def restore_mongodb(backup_path, uncompress=True):
    """
    Restore a MongoDB database from a backup.

        backup_path: The absolute path to a backup.
        uncompress: If True, the backup is assumed to be a gzipped tar and is
            uncompressed before the database restoration.
    """

    logging.info('Restoring MongoDB from "{}"'.format(backup_path))

    if uncompress:
        backup_path = _uncompress(backup_path)

    cmd = 'mongorestore {}'.format(backup_path)
    ret = subprocess.call(cmd, shell=True)
    if ret:  # if non-zero return
        error_msg = 'Error occurred while restoring MongoDB backup'
        logging.error(error_msg)
        raise Exception(error_msg)

    logging.info('MongoDB successfully restored')


def restore_mysql(backup_path, uncompress=True, settings=None):
    """
    Restore a MySQL database from a backup.

        backup_path: The absolute path to a backup.
        uncompress: If True, the backup is assumed to be a gzipped tar and is
            uncompressed before the database restoration.
    """

    logging.info('Restoring MySQL from "{}"'.format(backup_path))

    if uncompress:
        backup_path = _uncompress(backup_path)

    cmd = 'mysqladmin -f drop edxapp'
    ret = subprocess.call(cmd, shell=True)
    if ret:  # if non-zero return
        error_msg = 'Error occurred while deleting old mysql database'
        logging.error(error_msg)
        raise Exception(error_msg)

    cmd = 'mysqladmin -f create edxapp'
    ret = subprocess.call(cmd, shell=True)
    if ret:  # if non-zero return
        error_msg = 'Error occurred while creating new mysql database'
        logging.error(error_msg)
        raise Exception(error_msg)

    cmd = 'mysql -D edxapp < {0}'.format(backup_path)
    ret = subprocess.call(cmd, shell=True)
    if ret:  # if non-zero return
        error_msg = 'Error occurred while restoring mysql database'
        logging.error(error_msg)
        raise Exception(error_msg)

    cmd = ('source /edx/app/edxapp/edxapp_env && /edx/bin/manage.edxapp '
           'lms migrate --settings={} --delete-ghost-migrations'.format(settings))
    ret = subprocess.call(cmd, shell=True, executable="/bin/bash")
    if ret:  # if non-zero return
        error_msg = 'Error occurred while running edx migrations'
        logging.error(error_msg)
        raise Exception(error_msg)

    cmd = '/edx/bin/supervisorctl restart edxapp:'
    ret = subprocess.call(cmd, shell=True)
    if ret:  # if non-zero return
        error_msg = 'Error occurred while restarting edx'
        logging.error(error_msg)
        raise Exception(error_msg)

    logging.info('MySQL successfully restored')


def _uncompress(file_path):
    """
    Uncompress a gzipped tar file. The contents of the compressed file are
    extracted to the directory containing the compressed file.

        file_path: An absolute path to a gzipped tar file.

        returns: The directory containing the contents of the compressed file.
    """

    logging.info('Uncompressing file at "{}"'.format(file_path))

    file_dir = os.path.dirname(file_path)
    cmd = 'tar xzvf {}'.format(file_path)
    ret = subprocess.call(cmd, shell=True)
    if ret:  # if non-zero return
        error_msg = 'Error occurred while uncompressing {}'.format(file_path)
        logging.error(error_msg)
        raise Exception(error_msg)

    return file_path.replace('.tar.gz', '')


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('service', help='mongodb or mysql')
    parser.add_argument('-r', '--restore-path',
                        help='path to a backup used to restore a database')
    parser.add_argument('-d', '--dir', dest='backup_dir',
                        help='temporary storage directory used during backup')
    parser.add_argument('-p', '--provider', help='gs or s3')
    parser.add_argument('-b', '--bucket', help='bucket name')
    parser.add_argument('-i', '--s3-id', dest='s3_id',
                        help='AWS access key id')
    parser.add_argument('-k', '--s3-key', dest='s3_key',
                        help='AWS secret access key')
    parser.add_argument('-n', '--no-compress', dest='compress',
                        action='store_false', default=True,
                        help='disable compression')
    parser.add_argument('-s', '--settings',
                        help='Django settings used when running database '
                             'migrations')

    return parser.parse_args()


def _main():
    args = _parse_args()

    program_name = os.path.basename(sys.argv[0])
    backup_dir = (args.backup_dir or os.environ.get('BACKUP_DIR') or
                  '/tmp/db_backups')
    bucket = args.bucket or os.environ.get('BACKUP_BUCKET')
    compress = args.compress
    provider = args.provider or os.environ.get('BACKUP_PROVIDER') or 'gs'
    restore_path = args.restore_path
    s3_id = args.s3_id or os.environ.get('BACKUP_AWS_ACCESS_KEY_ID')
    s3_key = args.s3_key or os.environ.get('BACKUP_AWS_SECRET_ACCESS_KEY')
    settings = args.settings or os.environ.get('BACKUP_SETTINGS') or 'aws_appsembler'
    service = args.service

    if program_name == 'edx_backup':
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        backup_path = dump_service(service, backup_dir)

        if compress:
            backup_path = compress_backup(backup_path)

        if provider == 'gs':
            upload_to_gcloud_storage(backup_path, bucket)
        elif provider == 's3':
            upload_to_s3(backup_path, bucket, aws_access_key_id=s3_id,
                         aws_secret_access_key=s3_key)
        else:
            error_msg = 'Error occurred while compressing backup'
            logging.warning(error_msg)

        clean_up(backup_path.replace('.tar.gz', ''))

    elif program_name == 'edx_restore':
        restore(service, restore_path, settings=settings)

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    _main()
