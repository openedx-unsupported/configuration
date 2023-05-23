import boto3
from botocore.exceptions import ClientError
import backoff
import csv
import click
import sqlite3
import datetime

MAX_TRIES = 5

# for BUCKET in $(aws s3api list-buckets --output text --query 'Buckets[*].Name'); do echo $BUCKET; done


class S3BotoWrapper:
    def __init__(self):
        self.client = boto3.resource('s3')

    @backoff.on_exception(backoff.expo, ClientError, max_tries=MAX_TRIES)
    def list_buckets(self):
        return self.client.buckets.all()

    @backoff.on_exception(backoff.expo, ClientError, max_tries=MAX_TRIES)
    def get_bucket(self, bucket_name):
        return self.client.Bucket(bucket_name)

    @backoff.on_exception(backoff.expo, ClientError, max_tries=MAX_TRIES)
    def get_object(self, bucket_name, obj_key):
        return self.client.Object(bucket_name, obj_key)


@click.command()
@click.argument('bucket', required=True)
@click.argument('sqlite_file', required=True, type=str)
@click.option('--import_tsv_file', type=click.File('r'))
def controller(bucket, sqlite_file, import_tsv_file):

    if import_tsv_file:
        objects = csv.DictReader(import_tsv_file, ('bucket_name', 'key', 'encryption_status'), dialect='excel-tab')
    else:
        client = S3BotoWrapper()
        bucket_info = client.get_bucket(bucket)
        objects = bucket_info.objects.all()

    db = sqlite3.connect(sqlite_file)
  
    table_name = bucket.replace('-', '_').replace('.','_')
    # Keep real bucket name. Tables names can't be special characters like - or .
    # list_timestamp = timestamp when object was added to DB
    # encryption_timestamp = when we updated the encryption_status field
    db.execute(f"CREATE TABLE {table_name}(object_key PRIMARY KEY, bucket, encryption_status, list_timestamp, encryption_timestamp)")

    rows_written = 0

    for obj in objects:
       if import_tsv_file:
           row_data = {
               'bucket': obj['bucket_name'],
               'object_key': obj['key'],
               'encryption_status': 'Unknown',
               'list_timestamp': datetime.datetime.now(),
               'encryption_timestamp': None
           }
       else:
           row_data = {
               'bucket': obj.bucket_name,
               'object_key': obj.key,
               'encryption_status': 'Unknown',
               'list_timestamp': datetime.datetime.now(),
               'encryption_timestamp': None
           }
       db.execute(f"INSERT INTO {table_name} VALUES(:object_key, :bucket, :encryption_status, :list_timestamp, :encryption_timestamp)", row_data)
       db.commit()
       rows_written += 1

       if rows_written % 100 == 0:
           print(f"Rows written {rows_written}")

# Test code to stop after 2000 lines
#       if rows_written == 2000:
#           break

    db.commit()
    db.close()

if __name__ == '__main__':
    controller()

