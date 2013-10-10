import boto
import time

region = 'us-east-1'
stack_name = 'testautostack'
template = '/Users/feanil/src/configuration/cloudformation_templates/edx-reference-architecture.json'

def create_stack(stack_name,region='us-east-1',template_file):
  cfn = boto.connect_cloudformation()
  stack_id = cfn.create_stack(stack_name,
    stack_body=open(template).read(),
    capabilities=['CAPABILITIY_IAM'],
    notification_arns=['arn:aws:sns:us-east-1:372153017832:stack-creation-events'],
    tags={'autostack':'true'})
  
  while True:
    sleep(1)
    stack_instance = cfn.describe_stacks(stack_id)[0]
    status = stack_instance.stack_status
    if 'COMPLETE' in status:
      break
    else:
      print(status)


create_stack(stack_name, region, template)

print('Stack({}) created.'.format(stack_name))
  
# Create DNS for edxapp and xqueue.
dns_settings = {
  'edxapp'  : [ 'courses', 'studio' ],
  'xqueue'  : [ 'xqueue' ],
  'rabbit'  : [ 'rabbit' ],
  'xserver' : [ 'xserver' ],
  'worker'  : [ 'worker' ],
}

# Create a zone for the stack.
zone_name = "{}.vpc.edx.org".format(stack_name)

#TODO Make this a function instead of a class method.
zone = get_or_create_hosted_zone(zone_name)

elbs = boto.connect_elb()

#TODO Implement this.
stack_elbs = elbs_for_stack_name(stack_name)
for elb in stack_elbs:
  for service, dns_prefixes in dns_settings.items():
    if service in elb.dns_name.lower():
      for prefix in dns_prefixes:
        # TODO: Make this function.
        create_service_dns(elb, prefix, zone_name)



