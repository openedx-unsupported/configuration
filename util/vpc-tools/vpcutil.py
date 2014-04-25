import boto

def vpc_for_stack_name(stack_name, aws_id=None, aws_secret=None):
    cfn = boto.connect_cloudformation(aws_id, aws_secret)
    resources = cfn.list_stack_resources(stack_name)
    for resource in resources:
      if resource.resource_type == 'AWS::EC2::VPC':
        return resource.physical_resource_id

def stack_name_for_vpc(vpc_name):
    cfn_tag_key = 'aws:cloudformation:stack-name'
    vpc = boto.connect_vpc(aws_id, aws_secret)
    resource = vpc.get_all_vpcs(vpc_ids=[vpc_name])[0]
    if cfn_tag_key in resource.tags:
        return resource.tags[cfn_tag_key]
    else:
        msg = "VPC({}) is not part of a cloudformation stack.".format(vpc_name)
        raise Exception(msg)



