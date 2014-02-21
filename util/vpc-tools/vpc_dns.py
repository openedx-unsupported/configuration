#!/usr/bin/env python -u
#
# Updates DNS records for a stack
#
# Example usage:
#
#   # update route53 entries for ec2 and rds instances
#   # in the vpc with stack-name "stage-stack" and
#   # create DNS entries in the example.com hosted
#   # zone
#
#   python vpc_dns.py -s stage-stack -z example.com
#
#   # same thing but just print what will be done without
#   # making any changes
#
#   python vpc_dns.py -n -s stage-stack -z example.com
#
#   # Create a new zone "vpc.example.com", update the parent
#   # zone "example.com"
#
#   python vpc_dns.py -s stage-stack -z vpc.example.com
#

import argparse
import boto
import datetime
from vpcutil import vpc_for_stack_name
import xml.dom.minidom
import re

r53 = boto.connect_route53()


extra_play_dns = {"edxapp":["courses","studio"]}

class DNSRecord():

    def __init__(self, zone, record_name, record_type,
                         record_ttl, record_values):
        self.zone = zone
        self.record_name = record_name
        self.record_type = record_type
        self.record_ttl = record_ttl
        self.record_values = record_values

def add_or_update_record(dns_records):
    """
    Creates or updates a DNS record in a hosted route53
    zone
    """
    change_set = boto.route53.record.ResourceRecordSets()

    for record in dns_records:

        status_msg = """
        record_name:   {}
        record_type:   {}
        record_ttl:    {}
        record_values: {}
                 """.format(record.record_name, record.record_type,
                            record.record_ttl, record.record_values)

        if args.noop:
            print("Would have updated DNS record:\n{}".format(status_msg))

        zone_id = record.zone.Id.replace("/hostedzone/", "")

        records = r53.get_all_rrsets(zone_id)

        old_records = {r.name[:-1]: r for r in records}

        # If the record name already points to something.
        # Delete the existing connection.
        if record.record_name in old_records.keys():
            if args.force:
                print("Deleting record:\n{}".format(status_msg))
                change = change_set.add_change(
                    'DELETE',
                    record.record_name,
                    record.record_type,
                    record.record_ttl)
            else:
                raise RuntimeError(
                    "DNS record exists for {} and force was not specified.".
                    format(record.record_name))

            for value in old_records[record.record_name].resource_records:
                change.add_value(value)

        change = change_set.add_change(
            'CREATE',
            record.record_name,
            record.record_type,
            record.record_ttl)

        for value in record.record_values:
            change.add_value(value)

    if args.noop:
        print("Would have submitted the following change set:\n")
        xml_doc = xml.dom.minidom.parseString(change_set.to_xml())
        print xml_doc.toprettyxml()
    else:
        r53.change_rrsets(zone_id, change_set.to_xml())
        print("Updated DNS record:\n{}".format(status_msg))


def get_or_create_hosted_zone(zone_name):
    """
    Creates the zone and updates the parent
    with the NS information in the zone

    returns: created zone
    """

    zone = r53.get_hosted_zone_by_name(zone_name)
    parent_zone_name = ".".join(zone_name.split('.')[1:])
    parent_zone = r53.get_hosted_zone_by_name(parent_zone_name)

    if args.noop:
        if parent_zone:
            print("Would have created/updated zone: {} parent: {}".format(
                zone_name, parent_zone_name))
        else:
            print("Would have created/updated zone: {}".format(
                zone_name, parent_zone_name))
        return zone

    if not zone:
        print("zone {} does not exist, creating".format(zone_name))
        ts = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H:%M:%SUTC')
        zone = r53.create_hosted_zone(
            zone_name, comment="Created by vpc_dns script - {}".format(ts))

    if parent_zone:
        print("Updating parent zone {}".format(parent_zone_name))

        dns_records = set()
        dns_records.add(DNSRecord(parent_zone,zone_name,'NS',900,zone.NameServers))
        add_or_update_record(dns_records)

    return zone

def get_security_group_dns(group_name):
    # stage-edx-RabbitMQELBSecurityGroup-YB8ZKIZYN1EN
    environment,deployment,sec_group,salt = group_name.split('-')
    play = sec_group.replace("ELBSecurityGroup","").lower()
    return environment, deployment, play

def get_dns_from_instances(elb):

    ec2_con = boto.connect_ec2()

    for inst in elb.instances:
        instance = ec2_con.get_all_instances(
                instance_ids=[inst.id])[0].instances[0]
        try:
            env_tag = instance.tags['environment']
            if 'play' in instance.tags:
                play_tag = instance.tags['play']
            else:
                # deprecated, for backwards compatibility
                play_tag = instance.tags['role']

            break  # only need the first instance for tag info
        except KeyError:
            print("Instance {}, attached to elb {} does not "
                  "have tags for environment and play".format(elb, inst))
            raise

    return env_tag, play_tag


def update_elb_rds_dns(zone):
    """
    Creates elb and rds CNAME records
    in a zone for args.stack_name.
    Uses the tags of the instances attached
    to the ELBs to create the dns name
    """

    dns_records = set()

    elb_con = boto.connect_elb()
    rds_con = boto.connect_rds()

    vpc_id = vpc_for_stack_name(args.stack_name)

    if not zone and args.noop:
        # use a placeholder for zone name
        # if it doesn't exist
        zone_name = "<zone name>"
    else:
        zone_name = zone.Name[:-1]

    stack_elbs = [elb for elb in elb_con.get_all_load_balancers()
                  if elb.vpc_id == vpc_id]

    for elb in stack_elbs:

        if "RabbitMQ" in elb.source_security_group.name or "ElasticSearch" in elb.source_security_group.name:
            env_tag,deployment,play_tag = get_security_group_dns(elb.source_security_group.name)
            fqdn = "{}-{}.{}".format(env_tag, play_tag, zone_name)
            dns_records.add(DNSRecord(zone,fqdn,'CNAME',600,[elb.dns_name]))
        else:
            env_tag,play_tag = get_dns_from_instances(elb)
            fqdn = "{}-{}.{}".format(env_tag, play_tag, zone_name)
            dns_records.add(DNSRecord(zone,fqdn,'CNAME',600,[elb.dns_name]))

        if extra_play_dns.has_key(play_tag):
            for name in extra_play_dns.get(play_tag):
                fqdn = "{}-{}.{}".format(env_tag, name, zone_name)
                dns_records.add(DNSRecord(zone,fqdn,'CNAME',600,[elb.dns_name]))


    stack_rdss = [rds for rds in rds_con.get_all_dbinstances()
                  if hasattr(rds.subnet_group, 'vpc_id') and
                  rds.subnet_group.vpc_id == vpc_id]

    # TODO the current version of the RDS API doesn't support
    # looking up RDS instance tags.  Hence, we are using the 
    # env_tag that was set via the loop over instances above.
    for rds in stack_rdss:
        fqdn = "{}-{}.{}".format(env_tag,'rds', zone_name)
        dns_records.add(DNSRecord(zone,fqdn,'CNAME',600,[stack_rdss[0].endpoint[0]]))

    add_or_update_record(dns_records)

if __name__ == "__main__":
    description = "Give a cloudformation stack name, for an edx stack, setup \
        DNS names for the ELBs in the stack."

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-s', '--stack-name', required=True,
                        help="The name of the cloudformation stack.")
    parser.add_argument('-n', '--noop',
                        help="Don't make any changes.", action="store_true",
                        default=False)
    parser.add_argument('-z', '--zone-name', default="vpc.edx.org",
                        help="The name of the zone under which to "
                             "create the dns entries.")
    parser.add_argument('-f', '--force',
                        help="Force reuse of an existing name in a zone",
                        action="store_true",default=False)

    args = parser.parse_args()
    zone = get_or_create_hosted_zone(args.zone_name)
    update_elb_rds_dns(zone)

