import boto3
from botocore.exceptions import ClientError
import backoff
import csv

MAX_TRIES = 5


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


def objects_puller():
    client = S3BotoWrapper()
    obj_dict = {}
    temp_dict = {}
    for bucket in client.list_buckets():
        obj_dict[bucket.name] = {}
        bucket_info = client.get_bucket(bucket.name)
        for obj in bucket_info.objects.all():
            key = client.get_object(bucket.name, obj.key)
            if key.server_side_encryption is None:
                temp_dict[obj.key] = str(key.server_side_encryption)
        obj_dict[bucket.name] = temp_dict
    return obj_dict


def csv_writer(object_dict):
    with open('csv_file.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in object_dict.items():
            writer.writerow([key, value])


def controller():
    obj_dict = objects_puller()
    csv_writer(obj_dict)


if __name__ == '__main__':
    controller()

