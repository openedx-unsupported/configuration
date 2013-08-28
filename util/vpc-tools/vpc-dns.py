"""vpc-dns.py

Usage:
    vpc-dns.py create-zone (vpc <vpc_id> | stack-name <stack_name>)
    vpc-dns.py (-h --help)
    vpc-dns.py (-v --version)

Options:
    -h --help       Show this screen.
    -v --version    Show version.
"""
import boto
from boto.route53.record import ResourceRecordSets
from docopt import docopt
from vpcutil import vpc_for_stack_name

class VPCDns:
    BACKEND_ZONE = "Z4AI6ADZTL3HN"
    DNS_SUFFIX = ".vpc.edx.org"
    ZONE = "{name}" + DNS_SUFFIX

    def __init__(self,vpc_id=None):
        self.vpc_id = vpc_id
        self.elb = boto.connect_elb()
        self.r53 = boto.connect_route53()

    def create_zone(self, vpc_id):
        zone_name = self.ZONE.format(name=vpc_id)
        print zone_name
        hosted_zone = self.get_or_create_hosted_zone(zone_name)

        elbs = self.elb.get_all_load_balancers()

        for elb in [x for x in elbs if x.vpc_id == self.vpc_id]:
            self.create_service_dns(elb,self.get_zone_id_from_retval(
                hosted_zone.Id),self.vpc_id)

    def get_zone_id_from_retval(self,retval):
        """
        The data structure returned by the create_hosted_zone call
        pre-pends the string /hostedzone/ to the Id for some reason.
        """
        return retval.replace("/hostedzone/","")


    def get_or_create_hosted_zone(self, zone_name):

        hosted_zone = self.r53.get_hosted_zone_by_name(zone_name)

        if not hosted_zone:
            zone_data = self.r53.create_hosted_zone(zone_name,
                                        comment="Created by automation.")
            hosted_zone = self.r53.get_hosted_zone_by_name(zone_name)

        return hosted_zone


    def get_elb_service(self, elb):

        services = ["edxapp","rabbit","xqueue","xserver","worker"]

        for service in services:
            if service in elb.dns_name.lower():
                return service

        raise Exception("No service mapping for " + elb.dns_name)


    def create_service_dns(self, elb, zone, vpc_id):
        """
        """
        records = self.r53.get_all_rrsets(zone)

        old_names = [r.name for r in records]

        HOST_TEMPLATE = "{service}.{vpc_id}" + self.DNS_SUFFIX

        service = self.get_elb_service(elb)

        dns_name = HOST_TEMPLATE.format(service=service,
                                        vpc_id=vpc_id)

        change_set = ResourceRecordSets()

        if dns_name + '.' in old_names:
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

        self.r53.change_rrsets(zone, change_set.to_xml())

VERSION="0.1"

def dispatch(args):
    if args.get("vpc"):
      vpc_id = args.get("<vpc_id>")
    elif args.get("stack-name"):
      stack_name = args.get("<stack_name>")
      vpc_id = vpc_for_stack_name(stack_name)
    else:
      raise Exception("No vpc_id or stack_name provided.")

    c = VPCDns(vpc_id=vpc_id)

    if args.get("create-zone"):
        c.create_zone(vpc_id)

if __name__ == "__main__":
    args = docopt(__doc__, version=VERSION)
    dispatch(args)

