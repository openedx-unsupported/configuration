import boto
from vpcutil import vpc_for_stack_name

stack_name = 'testforumstack9'
# Utility Functions


def get_or_create_hosted_zone(zone_name):

  r53 = boto.connect_route53()
  hosted_zone = r53.get_hosted_zone_by_name(zone_name)

  if not hosted_zone:
    zone_data = r53.create_hosted_zone(zone_name,
        comment="Created by automation.")
    hosted_zone = r53.get_hosted_zone_by_name(zone_name)

  return hosted_zone

def elbs_for_stack_name(stack_name):
  vpc_id = vpc_for_stack_name(stack_name)
  elbs = boto.connect_elb()
  for elb in elbs.get_all_load_balancers():
    if elb.vpc_id == vpc_id:
      yield elb

def create_service_dns(elb, prefix, zone):
  # Get all record sets in zone
  r53 = boto.connect_route53(debug=2)

  zone_id = zone.Id.replace("/hostedzone/","") 
  records = r53.get_all_rrsets(zone_id)

  old_names = [r.name[:-1] for r in records]
  print(old_names)

  dns_template = "{prefix}.{zone_name}"

  # Have to remove the trailing period that is on zone names.
  zone_name = zone.Name[:-1]
  dns_name = dns_template.format(prefix=prefix,
                                 zone_name=zone_name)

  change_set = boto.route53.record.ResourceRecordSets()

  # If the dns name already points to something.
  # Delete the existing connection.
  print(dns_name)
  if dns_name in old_names:
    print "adding delete"
    change = change_set.add_change(
      'DELETE',
      dns_name,
      'CNAME',
      600)

    change.add_value(elb.dns_name)

  change = change_set.add_change(
    'CREATE',
    dns_name,
    'CNAME',
    600 )

  change.add_value(elb.dns_name)

  print change_set.to_xml()

  r53.change_rrsets(zone_id, change_set.to_xml())


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

zone = get_or_create_hosted_zone(zone_name)

stack_elbs = elbs_for_stack_name(stack_name)
for elb in stack_elbs:
  for service, dns_prefixes in dns_settings.items():
    if service in elb.dns_name.lower():
      for prefix in dns_prefixes:
        create_service_dns(elb, prefix, zone)
