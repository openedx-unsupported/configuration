from collections import defaultdict
import boto3
from botocore.exceptions import ClientError
import backoff
import csv
import click

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
#        if obj_key == '01250b70-62a1-4835-b73d-8110ed700193/01250b70-62a1-4835-b73d-8110ed700193-hls0720p_00002.ts':
#            raise
        return self.client.Object(bucket_name, obj_key)


@click.command()
@click.argument('input_tsv_file', required=True, type=click.File('r'))
@click.argument('output_tsv_file', required=True, type=click.File('w'))
@click.option('--filter-out-encrypted/--no-filter-out-encrypted', default=False, help="If enabled output file will not contain object keys that are already encrypted")
def controller(input_tsv_file, output_tsv_file, filter_out_encrypted):
    client = S3BotoWrapper()
    reader = csv.reader(input_tsv_file, dialect='excel-tab')
    writer = csv.writer(output_tsv_file, dialect='excel-tab')

    session_valid = True

    rows_read = 0
    rows_written = 0
    rows_not_written = 0
    rows_skipped = 0
    status_count = defaultdict(int)

    for bucket_name, object_key, encryption_status in reader:
        rows_read += 1
# Test code to simulate session failure
#        if rows_written > 250:
#            session_valid = False
        # SSE = Server Side Encryption
        object_sse = encryption_status

        # Unknown means we haven't checked yet, None means it's unencrypted
        if object_sse == 'Unknown':
            if session_valid:
                try:
                    object = client.get_object(bucket_name, object_key)
                    object_sse = str(object.server_side_encryption)
                except Exception as E:
                    print(f"On object key {object_key}, caught exception {E}")
                    session_valid = False
                    pass
                
        else:
            rows_skipped += 1

        if not filter_out_encrypted or object_sse in ['None', 'Unknown']:
            writer.writerow([bucket_name, object_key, object_sse])
            rows_written += 1
        else:
            rows_not_written += 1

        status_count[object_sse] += 1
        if rows_read % 100 == 0:
            sum_status_count = sum(status_count.values())
            print(f"SUM(status_count): {sum_status_count}, Rows read: {rows_read}, written: {rows_written}, not_written: {rows_not_written}, skipped: {rows_skipped}, status_count: {dict(status_count)}")

    sum_status_count = sum(status_count.values())

    print(f"SUM(status_count): {sum_status_count}, Rows read: {rows_read}, written: {rows_written}, not_written: {rows_not_written}, skipped: {rows_skipped}, status_count: {dict(status_count)}")
    print(f"Status count {dict(status_count)}")
    if sum_status_count != rows_read:
        print()
        print(f"WARNING!!! Output file may not be trustworthy, Sum of statuses ({sum_status_count}) does not equal number of rows read ({rows_read})")
    if rows_read != rows_written + rows_not_written:
        print()
        print(f"WARNING!!! Output file may not be trustworthy, Sum of rows_written and rows_not_written ({rows_written} + {rows_not_written} = {rows_written+rows_not_written}) does not equal number of rows read ({rows_read})")
    if not filter_out_encrypted and rows_read != rows_written:
        print()
        print(f"WARNING!!! Output file may not be trustworthy, rows_written does not equal number of rows read ({rows_read})")


if __name__ == '__main__':
    controller()

