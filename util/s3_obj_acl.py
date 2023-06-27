import csv
import sys

from botocore.exceptions import ClientError
import backoff
import click
import boto3
import concurrent.futures


MAX_TRIES = 5


class S3BotoWrapper:
    def __init__(self):
        self.client = boto3.client('s3')

    @backoff.on_exception(backoff.expo, ClientError, max_tries=MAX_TRIES)
    def get_object_acl(self, bucket_name, obj_key):
        return self.client.get_object_acl(Bucket=bucket_name, Key=obj_key)


def get_object_acl(bucket_name, object_name):
    client = S3BotoWrapper()
    try:
        # Get the ACL for the object
        response = client.get_object_acl(bucket_name, object_name)
        acl = response['Grants']
        return acl
    except Exception as e:
        print(f"Error retrieving ACL for {object_name}: {str(e)}")
        return None


def check_acl_uniformity(object_acls):
    # Extract the first object's ACL as the baseline
    baseline_acl = list(object_acls.values())[0]
    # for acl in object_acls.values():
    for key, acl in object_acls.items():
        print(key, acl)
        if acl != baseline_acl:
            print("ACL are not same")
            print(key, acl)
            return False

    return True


def read_csv_file(file_path):
    object_acls = {}
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        objects = list(reader)
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(get_object_acl, obj[0], obj[1]): obj for obj in objects}

        for future in concurrent.futures.as_completed(futures):
            obj = futures[future]
            acl = future.result()
            object_acls[(obj[0], obj[1])] = acl

    return object_acls


@click.command()
@click.option('--file_name', required=True, help='Use to identify the file name')
def controller(file_name):
    obj_dict = read_csv_file(file_name)
    is_acl_uniform = check_acl_uniformity(obj_dict)

    if is_acl_uniform:
        print("ACLs are the same for all objects in the bucket.")
    else:
        print("ACLs vary across objects in the bucket.")


if __name__ == '__main__':
    controller()

