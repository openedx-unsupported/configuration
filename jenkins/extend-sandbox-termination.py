__author__ = 'arbab'
'''
This script will be used to modify/extend the termination date on the sandbox.
'''
import boto
from datetime import datetime
from datetime import timedelta
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Modify/extend the termination date on the sandbox.")

    parser.add_argument('-n', '--noop', action='store_true',
                        help="don't actually run the commands", default=False)

    parser.add_argument('-p', '--profile', default=None,
                        help="AWS profile to use when connecting.")

    extend_group = parser.add_mutually_exclusive_group(required=True)

    extend_group.add_argument('-d', '--day', default=None,
                        help="number of days", type=int)

    extend_group.add_argument('-a', '--always', default=False,
                        help="Do not terminate this Sandbox")

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('-u', '--username', default=None,
                       help="GitHub username")

    group.add_argument('-c', '--custom', default=None,
                       help="Custom name, if the sandbox was not created with the default options")

    group.add_argument('-i', '--instance-id', default=None,
                       help="Sandbox Instance ID")

    args = parser.parse_args()

    ec2 = boto.connect_ec2(profile_name=args.profile)

    days_to_increase = args.day

    if args.username:
        sandbox_name = args.username + '-sandbox'
        reservations = ec2.get_all_instances(filters={"tag:Name": sandbox_name})
    if args.custom:
        sandbox_name = args.custom
        reservations = ec2.get_all_instances(filters={"tag:Name": sandbox_name})
    if args.instance_id:
        instance_id = args.instance_id
        reservations = ec2.get_all_instances(instance_ids=[instance_id])

    instance = reservations[0].instances[0]

    if args.noop:
        logger.info("Sandbox ID:{} with Name: {} and Owner: {} will extend by {} days".format(
                    instance.id,
                    instance.tags['Name'],
                    instance.tags['owner'],
                    days_to_increase
                    )
                    )
    elif args.always:
        instance.add_tag('do_not_terminate', 'true')
        logger.info("Sandbox ID:{} with Name: {} and Owner: {} will not be terminate".format(
                    instance.id,
                    instance.tags['Name'],
                    instance.tags['owner'],
                    )
                    )
    else:
        # modified the terminate time
        terminate_time = datetime.strptime(str(instance.tags['instance_termination_time']), "%m-%d-%Y %H:%M:%S")
        terminate_time = terminate_time + timedelta(days=days_to_increase)
        instance.add_tag('instance_termination_time', terminate_time.strftime("%m-%d-%Y %H:%M:%S"))
        logger.info("Sandbox ID:{} with Name: {} and Owner: {} has been extended by {} days".format(
                    instance.id,
                    instance.tags['Name'],
                    instance.tags['owner'],
                    days_to_increase
                    )
                    )