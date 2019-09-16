from __future__ import absolute_import
import boto
import boto.rds2
import boto.rds

CFN_TAG_KEY = 'aws:cloudformation:stack-name'

def vpc_for_stack_name(stack_name, aws_id=None, aws_secret=None):
    cfn = boto.connect_cloudformation(aws_id, aws_secret)
    resources = cfn.list_stack_resources(stack_name)
    for resource in resources:
        if resource.resource_type == 'AWS::EC2::VPC':
            return resource.physical_resource_id


def stack_name_for_vpc(vpc_name, aws_id, aws_secret):
    vpc = boto.connect_vpc(aws_id, aws_secret)
    resource = vpc.get_all_vpcs(vpc_ids=[vpc_name])[0]
    if CFN_TAG_KEY in resource.tags:
        return resource.tags[CFN_TAG_KEY]
    else:
        msg = "VPC({}) is not part of a cloudformation stack.".format(vpc_name)
        raise Exception(msg)


def rds_subnet_group_name_for_stack_name(stack_name, region='us-east-1', aws_id=None, aws_secret=None):
    # Helper function to look up a subnet group name by stack name
    rds = boto.rds2.connect_to_region(region)
    vpc = vpc_for_stack_name(stack_name)
    for group in rds.describe_db_subnet_groups()['DescribeDBSubnetGroupsResponse']['DescribeDBSubnetGroupsResult']['DBSubnetGroups']:
        if group['VpcId'] == vpc:
            return group['DBSubnetGroupName']
    return None


def all_stack_names(region='us-east-1', aws_id=None, aws_secret=None):
    vpc_conn = boto.connect_vpc(aws_id, aws_secret)
    return [vpc.tags[CFN_TAG_KEY] for vpc in vpc_conn.get_all_vpcs()
            if CFN_TAG_KEY in list(vpc.tags.keys())]
