import argparse
import boto
from os.path import basename
from time import sleep

region = 'us-east-1'
stack_name = 'testautostack'
bucket_name = 'edx-sandbox-devops2'
template = '/Users/feanil/src/configuration/cloudformation_templates/edx-reference-architecture.json'

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
  # May not be necessary.

  url = "https://s3.amazonaws.com/{}/{}".format(bucket_name, key_name)
  return url

def create_stack(stack_name, template, region='us-east-1', blocking=True):
  cfn = boto.connect_cloudformation()

  # Upload the template to s3
  key_name = "cloudformation/auto/{}_{}".format(stack_name, basename(template))
  template_url = upload_file(template, bucket_name, key_name)

  # Reference the stack.
  try:
    stack_id = cfn.create_stack(stack_name,
      template_url=template_url,
      capabilities=['CAPABILITY_IAM'],
      tags={'autostack':'true'},
      parameters=[("KeyName", "continuous-integration")])
  except Exception as e:
    print(e.message)
    raise e
  
  while blocking:
    sleep(5)
    stack_instance = cfn.describe_stacks(stack_id)[0]
    status = stack_instance.stack_status
    print(status)
    if 'COMPLETE' in status:
      break

  return stack_id

create_stack(stack_name, template, region)

print('Stack({}) created.'.format(stack_name))
