# Get the tags for this instance
import argparse
import boto
import boto.utils
import os
import subprocess


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Enable all services that are in the services tag of this ec2 instance.")
    parser.add_argument("-a","--available",
        help="The location of the available services.")
    parser.add_argument("-e","--enabled",
        help="The location of the enabled services.")

    args = parser.parse_args()

    ec2 = boto.connect_ec2()
    instance_id = boto.utils.get_instance_metadata()['instance-id']
    reservations = ec2.get_all_instances(instance_ids=[instance_id])
    report = []
    for reservation in reservations:
        for instance in reservation.instances:
            if instance.id == instance_id:
                services = instance.tags['services'].split(',')
                for service in services:
                    # Link to available service.
                    available_file = "{}/{}.conf".format(args.available, service)
                    link_location = "{}/{}.conf".format(args.enabled, service)
                    if os.path.exists(available_file):
                        subprocess.call("ln -sf {} {}".format(available_file, link_location), shell=True)
                        report.append("Linking service: {}".format(service))
                    else:
                        report.append("No conf available for service: {}".format(link_location))

    print("\n".join(report))
