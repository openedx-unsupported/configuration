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
def controller(input_tsv_file, output_tsv_file):
    client = S3BotoWrapper()
    reader = csv.reader(input_tsv_file, dialect='excel-tab')
    writer = csv.writer(output_tsv_file, dialect='excel-tab')

    session_valid = True

    for bucket_name, object_key, encryption_status in reader:
        # Unknown means we haven't checked yet, None means it's unencrypted
        if encryption_status in ['None', 'Unknown']:
            # SSE = Server Side Encryption
            object_sse = encryption_status
            if session_valid:
                try:
 #                   print(f"Try {object_key}")
                    object = client.get_object(bucket_name, object_key)
                    if object.server_side_encryption is None:
                        object_sse = 'None'
                except Exception as E:
                    print(E)
                    print(f"Except {object_key}")
                    session_valid = False
                    pass
                
#            print(f"bucket {bucket_name}, object_key {object_key}, encryption_status {object_sse}")
            if object_sse in ['None', 'Unknown']:
                writer.writerow([bucket_name, object_key, object_sse])
        else:
            print(f"Skipping {object_key}")


if __name__ == '__main__':
    controller()

