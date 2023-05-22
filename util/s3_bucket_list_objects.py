import boto3
from botocore.exceptions import ClientError
import backoff
import csv
import click

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
@click.argument('tsv_file', required=True, type=click.File('w'))
def controller(bucket, tsv_file):
    client = S3BotoWrapper()
    writer = csv.writer(tsv_file, dialect='excel-tab')
    bucket_info = client.get_bucket(bucket)
    for obj in bucket_info.objects.all():
      # Format bucket,object_key,encryption_status
      writer.writerow([bucket, obj.key, 'Unknown'])


if __name__ == '__main__':
    controller()

