#!/edx/bin/python.edxapp

import boto
import datetime
import os
import shutil
import socket
import subprocess
import sys

# first attempt at a basic script for dumping mongo and postgresql dbs
# and uploading them to S3
#
#  CMD to run in cron:
# 	sudo crontab -e
# 		#Open edX DB Backups 3AM EST Daily (tjk)
# 		0 8 * * * /edx/bin/edx_db_backup.py
#

# TODO: breakup large files into smaller chunks
# TODO: error handling
# TODO: use better shell wrapper - envoy?
# TODO: better command line API - clint?


BACKUPS_FOLDER = os.path.join('/tmp', 'db_backups')
S3_BUCKET = os.environ.get('EDX_BACKUPS_S3_BUCKET')
AWS_ACCESS_KEY_ID = os.environ.get('EDX_BACKUPS_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('EDX_BACKUPS_AWS_SECRET_ACCESS_KEY')
HOST_NAME = socket.gethostname()


def make_file_name(base_name):
    '''
    creates a file name based on provided host_name, base_name and date
        e.g. openedxlite12345_mysql_20140102
    '''
    return '{0}_{1}_{2}'.format(HOST_NAME, base_name, datetime.datetime.now().strftime("%Y%m%d"))


def upload_to_s3(file_name):
    '''
    use boto to upload 'file_name' to the specified S3_BUCKET
    '''
    conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    bucket = conn.lookup(S3_BUCKET)
    mp = bucket.initiate_multipart_upload(file_name)

    fp = open(os.path.join(BACKUPS_FOLDER, file_name), 'rb')
    mp.upload_part_from_file(fp, 1)

    fp.close()
    mp.complete_upload() 
    conn.close()


def compress_backup(backup_filename):
    compressed_backup_filename = '{0}.tar.gz'.format(backup_filename)
    backup_path = os.path.join(BACKUPS_FOLDER, backup_filename)
    compressed_backup_path = os.path.join(BACKUPS_FOLDER, compressed_backup_filename)
    zip_cmd = 'GZIP=-9  tar -zcvf {0} {1}'.format(compressed_backup_path, backup_path)
    ret = subprocess.call(zip_cmd, shell=True)
    if ret:  # if non-zero return
        print 'error while zipping mongodb'
        pass  # write to logs or send email???
    return compressed_backup_filename


def dump_service(service_name, compress=True):
    SERVICES = {
        'mysql': 'mysqldump -u root --all-databases > {0}',
        'mongodb': 'mongodump -o {0}',
    }

    service = SERVICES.get(service_name)
    if service:
        backup_filename = make_file_name(service_name)
        cmd = service.format(os.path.join(BACKUPS_FOLDER, backup_filename))
        ret = subprocess.call(cmd, shell=True)
        if ret:  # if non-zero return
            print 'error while dumping {0}'.format(service_name)
            return  # write to logs or send email???

        if compress:
            zip_filename = compress_backup(backup_filename)
            return zip_filename
        else:
            return backup_filename
    else:
        print 'service {0} not found'.format(service_name)
        return


def clean_up(backup_filename):
    if backup_filename.endswith('.tar.gz'):
        backup_path = os.path.join(BACKUPS_FOLDER, backup_filename)
        os.remove(backup_path)
        backup_filename = backup_filename.replace('.tar.gz', '')

    backup_path = os.path.join(BACKUPS_FOLDER, backup_filename)
    if os.path.isdir(backup_path):
        shutil.rmtree(backup_path)
    else:
        os.remove(backup_path)


def restore_mongodb(backup_filename, uncompress=True):
    backup_path = os.path.join(BACKUPS_FOLDER, backup_filename)
    if uncompress:
        cmd = 'tar xzvf {0}'.format(os.path.join(BACKUPS_FOLDER, backup_path))
        ret = subprocess.call(cmd, shell=True)
        backup_path = backup_filename.replace('.tar.gz', '')
        if ret:  # if non-zero return
            print 'error while uncompressing {0}'.format(backup_path)
            return False  # write to logs or send email???

    cmd = 'mongorestore {0}'.format(os.path.join(BACKUPS_FOLDER, backup_path))
    ret = subprocess.call(cmd, shell=True)
    if ret:  # if non-zero return
        print 'Error while trying to restore MongoDB backup'
        return False  # write to logs or send email???
    print "MongoDB successfully restored"
    return True


def restore_mysql(backup_filename, uncompress=True):
    backup_path = os.path.join(BACKUPS_FOLDER, backup_filename)
    if uncompress:
        cmd = 'tar xzvf {0}'.format(backup_path)
        ret = subprocess.call(cmd, shell=True)
        backup_path = backup_path.replace('.tar.gz', '')
        if ret:  # if non-zero return
            print 'error while uncompressing {0}'.format(backup_path)
            return False  # write to logs or send email???

    cmd = 'mysqladmin -f drop edxapp'
    ret = subprocess.call(cmd, shell=True)
    if ret:  # if non-zero return
        print 'error while deleting old mysql database'
        return False  # write to logs or send email???

    cmd = 'mysqladmin -f create edxapp'
    ret = subprocess.call(cmd, shell=True)
    if ret:  # if non-zero return
        print 'error while creating a new mysql database'
        return False  # write to logs or send email???

    cmd = 'mysql -D edxapp < {0}'.format(backup_path)
    ret = subprocess.call(cmd, shell=True)
    if ret:  # if non-zero return
        print 'error while restoring the mysql database'
        return False  # write to logs or send email???

    cmd = 'source /edx/app/edxapp/edxapp_env && /edx/bin/manage.edxapp lms migrate --settings=docker --delete-ghost-migrations'
    ret = subprocess.call(cmd, shell=True, executable="/bin/bash")
    if ret:  # if non-zero return
        print 'error while running edx migrations'
        return False  # write to logs or send email???

    cmd = '/edx/bin/supervisorctl restart edxapp:'
    ret = subprocess.call(cmd, shell=True)
    if ret:  # if non-zero return
        print 'error while restarting edx'
        return False  # write to logs or send email???


if __name__ == '__main__':
    if sys.argv[1] == "backup":
        mongo_dump = dump_service('mongodb')
        upload_to_s3(mongo_dump)
        clean_up(mongo_dump)
        mysql_dump = dump_service('mysql')
        upload_to_s3(mysql_dump)
        clean_up(mysql_dump)
    elif sys.argv[1] == "restore":
        restore_mongodb(sys.argv[2])
        restore_mysql(sys.argv[3])
    else:
        print "Usage: ./edx_backups.py backup|restore [mongodb_backup_path] [mysql_backup_path]"
