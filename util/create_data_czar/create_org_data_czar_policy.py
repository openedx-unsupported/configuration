"""
create_org_data_czar_policy.py

Creates an IAM group for an edX org and applies an S3 policy to that group
that allows for read-only access to the group.

"""

import argparse
import boto3
from botocore.exceptions import ClientError
from string import Template
import sys

template = Template("""{
 "Version":"2012-10-17",
 "Statement": [
     {
     "Sid": "AllowListingOfOrgFolder",
     "Action": ["s3:ListBucket"],
     "Effect": "Allow",
     "Resource": ["arn:aws:s3:::edx-course-data"],
     "Condition":{"StringLike":{"s3:prefix":["$org","$org/*"]}}
     },
     {
      "Sid": "AllowGetBucketLocation",
      "Action": ["s3:GetBucketLocation"],
      "Effect": "Allow",
      "Resource": ["arn:aws:s3:::edx-course-data"]
     },
     {
     "Sid": "AllowGetS3ActionInOrgFolder",
     "Effect": "Allow",
     "Action": ["s3:GetObject"],
     "Resource": ["arn:aws:s3:::edx-course-data/$org/*"]
     }
 ]
}""")


def add_org_group(org, iam_connection):
        group_name = "edx-course-data-{org}".format(org=org)

        try:
            iam_connection.create_group(GroupName=group_name)
        except ClientError as bse:
            if bse.response['ResponseMetadata']['HTTPStatusCode'] == 409:
                pass
            else:
                print(bse)

        try:
            iam_connection.put_group_policy(
                GroupName=group_name,
                PolicyName=group_name,
                PolicyDocument=template.substitute(org=org)
            )
        except boto.exception.BotoServerError as bse:
            if bse.response['ResponseMetadata']['HTTPStatusCode'] == 409:
                pass
            else:
                print(bse)
                print(template.substitute(org=org))


parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument('-o', '--org', help='Name of the org for which to create an IAM '
                                       'role and policy, this should have the same '
                                       'name as the S3 bucket')
group.add_argument('-f', '--file', help='The path to a file containing one org name '
                                        'per line.')

args = parser.parse_args()

iam_connection = boto3.client('iam')
if args.org:
        add_org_group(args.org.rstrip('\n').lower(), iam_connection)
elif args.file:
    with open(args.file) as file:
        for line in file:
            org = line.rstrip('\n').lower()
            add_org_group(org, iam_connection)
else:
    parser.print_usage()
    sys.exit(1)

sys.exit(0)
