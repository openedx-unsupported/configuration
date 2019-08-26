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

from __future__ import absolute_import
from __future__ import print_function
import argparse
import boto
import datetime
from vpcutil import vpc_for_stack_name
import xml.dom.minidom
import sys

# These are ELBs that we do not want to create dns entries
# for because the instances attached to them are also in
# other ELBs and we want the env-deploy-play tuple which makes
# up the dns name to be unique

ELB_BAN_LIST = [
    'Apros',
]

# If the ELB name has the key in its name these plays
# will be used for the DNS CNAME tuple.  This is used for
# commoncluster.

ELB_PLAY_MAPPINGS = {
    'RabbitMQ': 'rabbitmq',
    'Xqueue': 'xqueue',
    'Elastic': 'elasticsearch',
}


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
    record_names = set()

    for record in dns_records:

        status_msg = """
        record_name:   {}
        record_type:   {}
        record_ttl:    {}
        record_values: {}
                 """.format(record.record_name, record.record_type,
                            record.record_ttl, record.record_values)
        if args.noop:
            print(("Would have updated DNS record:\n{}".format(status_msg)))
        else:
            print(("Updating DNS record:\n{}".format(status_msg)))

        if record.record_name in record_names:
            print(("Unable to create record for {} with value {} because one already exists!".format(
                record.record_values, record.record_name)))
            sys.exit(1)
        record_names.add(record.record_name)

        zone_id = record.zone.Id.replace("/hostedzone/", "")

        records = r53.get_all_rrsets(zone_id)

        old_records = {r.name[:-1]: r for r in records}

        # If the record name already points to something.
        # Delete the existing connection. If the record has
        # the same type and name skip it.
        if record.record_name in list(old_records.keys()):
            if record.record_name + "." == old_records[record.record_name].name and \
                    record.record_type == old_records[record.record_name].type:
                print(("Record for {} already exists and is identical, skipping.\n".format(
                    record.record_name)))
                continue

            if args.force:
                print(("Deleting record:\n{}".format(status_msg)))
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
    else:
        print("Submitting the following change set:\n")
    xml_doc = xml.dom.minidom.parseString(change_set.to_xml())
    print((xml_doc.toprettyxml(newl='')))  # newl='' to remove extra newlines
    if not args.noop:
        r53.change_rrsets(zone_id, change_set.to_xml())


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
            print(("Would have created/updated zone: {} parent: {}".format(
                zone_name, parent_zone_name)))
        else:
            print(("Would have created/updated zone: {}".format(
                zone_name, parent_zone_name)))
        return zone

    if not zone:
        print(("zone {} does not exist, creating".format(zone_name)))
        ts = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H:%M:%SUTC')
        zone = r53.create_hosted_zone(
            zone_name, comment="Created by vpc_dns script - {}".format(ts))

    if parent_zone:
        print(("Updating parent zone {}".format(parent_zone_name)))

        dns_records = set()
        dns_records.add(DNSRecord(parent_zone, zone_name, 'NS', 900, zone.NameServers))
        add_or_update_record(dns_records)

    return zone


def get_security_group_dns(group_name):
    # stage-edx-RabbitMQELBSecurityGroup-YB8ZKIZYN1EN
    environment, deployment, sec_group, salt = group_name.split('-')
    play = sec_group.replace("ELBSecurityGroup", "").lower()
    return environment, deployment, play


def get_dns_from_instances(elb):
    for inst in elb.instances:
        try:
            instance = ec2_con.get_all_instances(
                instance_ids=[inst.id])[0].instances[0]
        except IndexError:
            print(("instance {} attached to elb {}".format(inst, elb)))
            sys.exit(1)
        try:
            env_tag = instance.tags['environment']
            deployment_tag = instance.tags['deployment']
            if 'play' in instance.tags:
                play_tag = instance.tags['play']
            else:
                # deprecated, for backwards compatibility
                play_tag = instance.tags['role']
            break  # only need the first instance for tag info
        except KeyError:
            print(("Instance {}, attached to elb {} does not "
                  "have a tag for environment, play or deployment".format(inst, elb)))
            sys.exit(1)

    return env_tag, deployment_tag, play_tag


def update_elb_rds_dns(zone):
    """
    Creates elb and rds CNAME records
    in a zone for args.stack_name.
    Uses the tags of the instances attached
    to the ELBs to create the dns name
    """

    dns_records = set()

    vpc_id = vpc_for_stack_name(args.stack_name, args.aws_id, args.aws_secret)

    if not zone and args.noop:
        # use a placeholder for zone name
        # if it doesn't exist
        zone_name = "<zone name>"
    else:
        zone_name = zone.Name[:-1]

    stack_elbs = [elb for elb in elb_con.get_all_load_balancers()
                  if elb.vpc_id == vpc_id]
    for elb in stack_elbs:
        env_tag, deployment_tag, play_tag = get_dns_from_instances(elb)

        # Override the play tag if a substring of the elb name
        # is in ELB_PLAY_MAPPINGS

        for key in ELB_PLAY_MAPPINGS.keys():
            if key in elb.name:
                play_tag = ELB_PLAY_MAPPINGS[key]
                break
        fqdn = "{}-{}-{}.{}".format(env_tag, deployment_tag, play_tag, zone_name)

        # Skip over ELBs if a substring of the ELB name is in
        # the ELB_BAN_LIST

        if any(name in elb.name for name in ELB_BAN_LIST):
            print(("Skipping {} because it is on the ELB ban list".format(elb.name)))
            continue

        dns_records.add(DNSRecord(zone, fqdn, 'CNAME', 600, [elb.dns_name]))

    stack_rdss = [rds for rds in rds_con.get_all_dbinstances()
                  if hasattr(rds.subnet_group, 'vpc_id') and
                  rds.subnet_group.vpc_id == vpc_id]

    # TODO the current version of the RDS API doesn't support
    # looking up RDS instance tags.  Hence, we are using the
    # env_tag and deployment_tag that was set via the loop over instances above.

    rds_endpoints = set()
    for rds in stack_rdss:
        endpoint = stack_rdss[0].endpoint[0]
        fqdn = "{}-{}-{}.{}".format(env_tag, deployment_tag, 'rds', zone_name)
        # filter out rds instances with the same endpoints (multi-AZ)
        if endpoint not in rds_endpoints:
            dns_records.add(DNSRecord(zone, fqdn, 'CNAME', 600, [endpoint]))
        rds_endpoints.add(endpoint)

    add_or_update_record(dns_records)

if __name__ == "__main__":
    description = """

    Give a cloudformation stack name, for an edx stack, setup
    DNS names for the ELBs in the stack

    DNS entries will be created with the following format

       <environment>-<deployment>-<play>.edx.org

    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-s', '--stack-name', required=True,
                        help="The name of the cloudformation stack.")
    parser.add_argument('-n', '--noop',
                        help="Don't make any changes.", action="store_true",
                        default=False)
    parser.add_argument('-z', '--zone-name', default="edx.org",
                        help="The name of the zone under which to "
                             "create the dns entries.")
    parser.add_argument('-f', '--force',
                        help="Force reuse of an existing name in a zone",
                        action="store_true", default=False)
    parser.add_argument('--aws-id', default=None,
                        help="read only aws key for fetching instance information"
                             "the account you wish add entries for")
    parser.add_argument('--aws-secret', default=None,
                        help="read only aws id for fetching instance information for"
                             "the account you wish add entries for")

    args = parser.parse_args()
    # Connect to ec2 using the provided credentials on the commandline
    ec2_con = boto.connect_ec2(args.aws_id, args.aws_secret)
    elb_con = boto.connect_elb(args.aws_id, args.aws_secret)
    rds_con = boto.connect_rds(args.aws_id, args.aws_secret)

    # Connect to route53 using the user's .boto file
    r53 = boto.connect_route53()

    zone = get_or_create_hosted_zone(args.zone_name)
    update_elb_rds_dns(zone)
