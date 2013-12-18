import argparse
import boto
from os.path import basename
from time import sleep

FAILURE_STATES = [
    'CREATE_FAILED',
    'ROLLBACK_IN_PROGRESS',
    'ROLLBACK_FAILED',
    'ROLLBACK_COMPLETE',
    'DELETE_IN_PROGRESS',
    'DELETE_FAILED',
    'DELETE_COMPLETE',
    ]

def upload_file(file_path, bucket_name, key_name):
    """
    Upload a file to the given s3 bucket and return a template url.
    """
    conn = boto.connect_s3()
    try:
        bucket = conn.get_bucket(bucket_name)
    except boto.exception.S3ResponseError as e:
        conn.create_bucket(bucket_name)
        bucket = conn.get_bucket(bucket_name, validate=False)

    key = boto.s3.key.Key(bucket)
    key.key = key_name 
    key.set_contents_from_filename(file_path)

    url = 'https://s3.amazonaws.com/{}/{}'.format(bucket_name, key_name)
    return url

def create_stack(stack_name, template, region='us-east-1', blocking=True, temp_bucket='edx-sandbox-devops'):
    cfn = boto.connect_cloudformation()

    # Upload the template to s3
    key_name = 'cloudformation/auto/{}_{}'.format(stack_name, basename(template))
    template_url = upload_file(template, temp_bucket, key_name)

    # Reference the stack.
    try:
        stack_id = cfn.create_stack(stack_name,
            template_url=template_url,
            capabilities=['CAPABILITY_IAM'],
            tags={'autostack':'true'},
            parameters=[('KeyName', 'continuous-integration')])
    except Exception as e:
        print(e.message)
        raise e

   
    status = None 
    while blocking:
        sleep(5)
        stack_instance = cfn.describe_stacks(stack_id)[0]
        status = stack_instance.stack_status
        print(status)
        if 'COMPLETE' in status:
            break

    if status in FAILURE_STATES:
        raise Exception('Creation Failed. Stack Status: {}, ID:{}'.format(
            status, stack_id))

    return stack_id


if __name__ == '__main__':
        description = 'Create a cloudformation stack from a template.'
        parser = argparse.ArgumentParser(description=description)

        msg = 'Name for the cloudformation stack.'
        parser.add_argument('-n', '--stackname', required=True, help=msg)

        msg = 'Name of the bucket to use for temporarily uploading the \
            template.'
        parser.add_argument('-b', '--bucketname', default="edx-sandbox-devops",
            help=msg)

        msg = 'The path to the cloudformation template.'
        parser.add_argument('-t', '--template', required=True, help=msg)
       
        msg = 'The AWS region to build this stack in.'
        parser.add_argument('-r', '--region', default='us-east-1', help=msg)
       
        args = parser.parse_args() 
        stack_name = args.stackname
        template = args.template
        region = args.region
        bucket_name = args.bucketname

        create_stack(stack_name, template, region, bucket_name)
        print('Stack({}) created.'.format(stack_name))
