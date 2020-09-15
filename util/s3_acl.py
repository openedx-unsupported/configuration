#!/usr/bin/python3
"""
Get current ACL of all objects in given S3 bucket or set them to private or revert back.
Script supports 3 operations
1- getacl
2- setaclprivate
3- revertacl

1 optional parameter
whitelist (optional) (provide multiple whitelist parameters to filter out)

It saves current ACL in a file named bucketname.txt for updating or reverting purposes.

python s3_acl.py --bucketname <name-of-bucket> --operation getacl --whitelist <prefix_to_avoid>

Should assume role to run this script.
"""


import boto3
from botocore.exceptions import ClientError
import backoff
import sys
import json
import click
import logging

MAX_TRIES = 5
region = "us-east-1"
# Set logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# create file handler that logs messages
filehandler = logging.FileHandler('s3_acl.log')
filehandler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
filehandler.setFormatter(formatter)
# add the handlers to logger
logger.addHandler(filehandler)


class S3BotoWrapper:
    def __init__(self, **kwargs):
        self.client = boto3.client("s3", **kwargs)

    @backoff.on_exception(backoff.expo,
                          ClientError,
                          max_tries=MAX_TRIES)
    def get_object(self, *args, **kwargs):
        return self.client.list_objects_v2(*args, **kwargs)

    @backoff.on_exception(backoff.expo,
                          ClientError,
                          max_tries=MAX_TRIES)
    def get_acl(self, *args, **kwargs):
        return self.client.get_object_acl(*args, **kwargs)

    @backoff.on_exception(backoff.expo,
                          ClientError,
                          max_tries=MAX_TRIES)
    def put_acl(self, *args, **kwargs):
        return self.client.put_object_acl(*args, **kwargs)


def get_all_s3_keys(s3_bucket, region, whitelist):
    """Get a list of all keys in an S3 bucket."""
    keys = []
    kwargs = {'Bucket': s3_bucket}
    while True:
        s3_client = S3BotoWrapper(region_name=region)
        resp = s3_client.get_object(**kwargs)
        for obj in resp['Contents']:
            # Filter out directories, you can add more filters here if required.
            if obj['Key'][-1] == '/' or any(obj['Key'].startswith(whitelist_object) for whitelist_object in whitelist):
                continue
            else:
                keys.append(obj['Key'])
        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break
    return keys


def set_acl_private(acl_list, bucket_name, whitelist):
    s3_client = S3BotoWrapper(region_name=region)
    for item in acl_list:
        for key, value in item.items():
            if any(key.startswith(whitelist_object) for whitelist_object in whitelist):
                continue
            else:
                try:
                    s3_client.put_acl(
                        ACL='private',
                        Bucket=bucket_name,
                        Key=key,
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchKey':
                        logger.warning("No such key in S3: " + key)  # Will send the errors to the file
                    else:
                        logger.error(("Unexpected error :{}".format(e)))
                        sys.exit(1)


def revert_s3_acl(acl_list, bucket_name, whitelist):
    s3_client = S3BotoWrapper(region_name=region)
    for item in acl_list:
        for key, value in item.items():
            if any(key.startswith(whitelist_object) for whitelist_object in whitelist):
                continue
            else:
                try:
                    value.pop('ResponseMetadata', None)
                    s3_client.put_acl(
                        AccessControlPolicy=value,
                        Bucket=bucket_name,
                        Key=key,
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchKey':
                        logger.warning("No such key in S3: " + key)  # Will send the errors to the file
                    else:
                        logger.error(("Unexpected error :{}".format(e)))
                        sys.exit(1)


def get_s3_acl(s3_bucket, whitelist):
    s3_client = S3BotoWrapper(region_name=region)
    response_list = []
    try:
        s3_objects_key = get_all_s3_keys(s3_bucket, region, whitelist)
    except ClientError as e:
        logger.error(("Unable to connect to AWS with error :{}".format(e)))
        sys.exit(1)
    for object_key in s3_objects_key:
        try:
            temp = {}
            response = s3_client.get_acl(Bucket=s3_bucket, Key=object_key)
            temp[object_key] = response
            response_list.append(temp)
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                logger.warning("You Don't have permission to access this object: " + object_key)
            elif e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning("No such key in S3: " + object_key)  # Will send the errors to the file
            else:
                logger.error(("Unexpected error :{}".format(e)))
                sys.exit(1)
    return response_list


@click.command()
@click.option('--bucketname', required=True, help='S3 bucket name')
@click.option('--operation', required=True, help='Operation name to perform i.e 1- getacl 2- setaclprivate 3- revertacl')
@click.option('--whitelist', '-i', multiple=True, help='S3 objects name to avoid')
def controller(bucketname, operation, whitelist):
    file_to_write = bucketname + ".txt"
    if operation == 'getacl':
        objects_acl = get_s3_acl(bucketname, whitelist)
        with open(file_to_write, 'w') as fout:
            json.dump(objects_acl, fout)
        logger.info("Task completed. Total numbers of objects read are: " + str(len(objects_acl)))
    elif operation == 'setaclprivate':
        try:
            data = []
            with open(file_to_write, "r") as inFile:
                data = json.load(inFile)
            set_acl_private(data, bucketname, whitelist)
            logger.info("Task completed. ACL of " + bucketname + " objects set to private.")
        except IOError:
            logger.error("File not accessible")
            sys.exit(1)
    elif operation == 'revertacl':
        try:
            data = []
            with open(file_to_write, "r") as inFile:
                data = json.load(inFile)
            revert_s3_acl(data, bucketname, whitelist)
            logger.info("Task completed. ACL of " + bucketname + " objects reverted to given state")
        except IOError:
            logger.error("File not accessible")
            sys.exit(1)
    else:
        logger.error("Invalid Operation. Please enter valid operation. Operation supported are i.e 1- getacl "
                     "2- setaclprivate 3- revertacl ")  # Will send the errors to the file
        sys.exit(0)


if __name__ == '__main__':
    controller()

