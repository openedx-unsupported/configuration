import boto

def vpc_for_stack_name(stack_name):
    cfn = boto.connect_cloudformation()
    resources = cfn.list_stack_resources(stack_name)
    for resource in resources:
      if resource.resource_type == 'AWS::EC2::VPC':
        return resource.physical_resource_id

