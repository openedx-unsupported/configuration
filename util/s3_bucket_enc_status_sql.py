from collections import defaultdict
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
        session = boto3.Session()
        self.client = session.resource('s3')

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
def controller(bucket, sqlite_file):
    client = S3BotoWrapper()

    db = sqlite3.connect(sqlite_file)
    table_name = bucket.replace('-', '_').replace('.','_')

    # Unknown means we haven't checked yet, None means it's unencrypted
    objects_table = db.execute(f"SELECT object_key, bucket, encryption_status from {table_name} WHERE encryption_status == \"Unknown\"") 

    session_valid = True

    rows_read = 0
    rows_written = 0
    status_count = defaultdict(int)

    current_time = datetime.datetime.now()
    for object_key, bucket_name, encryption_status in objects_table:
        pass
        rows_read += 1
# Test code to stop after 1000 rows
#        if rows_written > 1000:
#            session_valid = False
        # SSE = Server Side Encryption
        object_sse = encryption_status

        if session_valid:
            try:
                object = client.get_object(bucket_name, object_key)
                object_sse = str(object.server_side_encryption)
            except Exception as E:
                print(f"On object key {object_key}, caught exception {E}")
                session_valid = False
                break
                pass
        else:
            break

        row_data = {'encryption_status': object_sse, 'object_key': object_key, 'encryption_timestamp': datetime.datetime.now()}
        update_cursor = db.execute(f"UPDATE {table_name} SET encryption_status = :encryption_status, encryption_timestamp = :encryption_timestamp WHERE object_key = :object_key", row_data)
        if update_cursor.rowcount != 1:
            print(f"ERROR!!! Update for {object_key} rowcount was {update_cursor.rowcount} instead of the expected 1")
            break
        rows_written += 1

        status_count[object_sse] += 1
        rows_between_prints = 1000
        if rows_read % rows_between_prints == 0:
            db.commit()
            sum_status_count = sum(status_count.values())
            previous_time = current_time
            current_time = datetime.datetime.now()
            print(f"SUM(status_count): {sum_status_count:,}, Rows read: {rows_read:,}, written: {rows_written:,}, {rows_between_prints:,} rows written in {current_time - previous_time}, status_count: {dict(status_count)}")

    db.commit()
    db.close()

    sum_status_count = sum(status_count.values())

    print(f"SUM(status_count): {sum_status_count:,}, Rows read: {rows_read:,}, written: {rows_written:,}, status_count: {dict(status_count)}")


if __name__ == '__main__':
    controller()

