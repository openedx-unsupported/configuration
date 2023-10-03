import csv
import sys
import urllib.parse
import logging
from botocore.exceptions import ClientError
import backoff
import click
import boto3
import concurrent.futures


MAX_TRIES = 5
inconsistent_acl_objects = []
consistent_acl_objects = []


# logging config

# Set logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# create file handler that logs messages
filehandler = logging.FileHandler('result.txt')
filehandler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(message)s')
filehandler.setFormatter(formatter)
# add the handlers to logger
logger.addHandler(filehandler)


class S3BotoWrapper:
    def __init__(self):
        self.client = boto3.client('s3')

    @backoff.on_exception(backoff.expo, ClientError, max_tries=MAX_TRIES)
    def get_object_acl(self, bucket_name, obj_key):
        return self.client.get_object_acl(Bucket=bucket_name, Key=obj_key)


def get_object_acl(bucket_name, object_name):
    client = S3BotoWrapper()
    try:
        # Try encoding
        object_name_decoded = urllib.parse.unquote(object_name)
        # Get the ACL for the object
        response = client.get_object_acl(bucket_name, object_name_decoded)
        acl = response['Grants']
        return acl
    except Exception as e:
        print(f"Error retrieving ACL for {object_name_decoded}: {str(e)}")
        return None


def check_acl_uniformity(object_acls):
    # Extract the first object's ACL as the baseline
    baseline_acl = list(object_acls.values())[0]
    # for acl in object_acls.values():
    for key, acl in object_acls.items():
        if acl != baseline_acl:
            acl_dict = {key: acl}
            inconsistent_acl_objects.append(acl_dict)
            # return False
        else:
            acl_cons_dict = {key: acl}
            consistent_acl_objects.append(acl_cons_dict)

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
    logger.info("Objects with same acl")
    for obj in consistent_acl_objects:
        logger.info(obj)
    logger.info("\n\nObjects with different acl")
    for in_obj in inconsistent_acl_objects:
        logger.info(in_obj)


if __name__ == '__main__':
    controller()
