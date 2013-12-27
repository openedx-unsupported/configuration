import argparse
import boto
from vpcutil import vpc_for_stack_name
from pprint import pprint

r53 = boto.connect_route53()


# Utility Functions
def add_or_update_record(zone, record_name, record_type, record_ttl, record_values):
    zone_id = zone.Id.replace("/hostedzone/","")

    records = r53.get_all_rrsets(zone_id)

    old_records = { r.name[:-1] : r for r in records }
    pprint(old_records)

    change_set = boto.route53.record.ResourceRecordSets()

    # If the record name already points to something.
    # Delete the existing connection.
    if record_name in old_records.keys():
        print "adding delete"
        change = change_set.add_change(
            'DELETE',
            record_name,
            record_type,
            record_ttl)

        for value in old_records[record_name].resource_records:
            change.add_value(value)

    change = change_set.add_change(
        'CREATE',
        record_name,
        record_type,
        record_ttl)

    for value in record_values:
        change.add_value(value)
     
    print(change_set.to_xml())
    r53.change_rrsets(zone_id, change_set.to_xml())


def add_zone_to_parent(zone, parent):
    #Add a reference for the new zone to its parent zone.
    parent_name = parent.Name[:-1]
    zone_name = zone.Name[:-1]

    add_or_update_record(parent, zone_name, 'NS', 900, zone.NameServers)


def get_or_create_hosted_zone(zone_name):
    # Get the parent zone.
    parent_zone_name = ".".join(zone_name.split('.')[1:])
    parent_zone = r53.get_hosted_zone_by_name(parent_zone_name)
    if not parent_zone:
        msg = "Parent zone({}) does not exist."
        raise Exception(msg.format(parent_zone_name))

    hosted_zone = r53.get_hosted_zone_by_name(zone_name)

    if not hosted_zone:
        r53.create_hosted_zone(zone_name,
                               comment="Created by automation.")
        hosted_zone = r53.get_hosted_zone_by_name(zone_name)

    add_zone_to_parent(hosted_zone, parent_zone)

    return hosted_zone


def elbs_for_stack_name(stack_name):
    vpc_id = vpc_for_stack_name(stack_name)
    elbs = boto.connect_elb()
    for elb in elbs.get_all_load_balancers():
        if elb.vpc_id == vpc_id:
            yield elb

def rdss_for_stack_name(stack_name):
    vpc_id = vpc_for_stack_name(stack_name)
    rds = boto.connect_rds()
    for instance in rds.get_all_dbinstances():
        if hasattr(instance, 'VpcId') and instance.VpcId == vpc_id:
            yield instance

def ensure_service_dns(generated_dns_name, prefix, zone):
    dns_template = "{prefix}.{zone_name}"

    # Have to remove the trailing period that is on zone names.
    zone_name = zone.Name[:-1]
    dns_name = dns_template.format(prefix=prefix,
                                   zone_name=zone_name)

    add_or_update_record(zone, dns_name, 'CNAME', 600, [generated_dns_name])


if __name__ == "__main__":
    description = "Give a cloudformation stack name, for an edx stack, setup \
        DNS names for the ELBs in the stack."

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-n', '--stackname',
        help="The name of the cloudformation stack.",
        required=True)

    parser.add_argument('-z', '--parent-zone',
        help="The parent zone under which the dns for this vpc resides.")
    args = parser.parse_args()
    stack_name = args.stackname

    # Create DNS for edxapp and xqueue.
    elb_dns_settings = {
        'edxapp': ['courses', 'studio'],
        'xqueue': ['xqueue'],
        'rabbit': ['rabbit'],
        'xserver': ['xserver'],
        'worker': ['worker'],
        'forum': ['forum'],
    }

    # Create a zone for the stack.
    parent_zone = 'vpc.edx.org'
    if args.parent_zone:
        parent_zone = args.parent_zone
    zone_name = "{}.{}".format(stack_name, parent_zone)

    zone = get_or_create_hosted_zone(zone_name)

    stack_elbs = elbs_for_stack_name(stack_name)
    for elb in stack_elbs:
        for role, dns_prefixes in elb_dns_settings.items():
            #FIXME this breaks when the service name is in the stack name ie. testforumstack.
            # Get the tags for the instances in this elb and compare the service against the role tag.
            if role in elb.dns_name.lower():
                for prefix in dns_prefixes:
                    ensure_service_dns(elb.dns_name, prefix, zone)


    # Add a DNS name for the RDS
    stack_rdss = list(rdss_for_stack_name(stack_name))
    if len(stack_rdss) != 1:
        msg = "Didn't find exactly one RDS in this VPC(Found {})"
        raise Exception(msg.format(len(stack_rdss)))
    else:
        ensure_service_dns(stack_rdss[0].endpoint[0], 'rds', zone)
