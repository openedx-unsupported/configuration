#!/usr/bin/env python

"""
Build an ansible inventory list suitable for use by -i by finding the active
Auto Scaling Group in an Elastic Load Balancer.  

If multiple ASGs are active in the ELB, no inventory is returned.

Assuming a single active ASG is found, a single machine is returned.  This inventory
is generally used to target a single machine in a cluster to run a cmomand.

Typical reponse:

10.2.42.79,

Typical use

ansible -i $(active_instances_in_asg.py --asg stage-edx-edxapp) -m shell -a 'management command'

"""

from __future__ import print_function
import argparse
import botocore.session
import botocore.exceptions
import sys
from collections import defaultdict
from os import environ

class ActiveInventory():

    profile = None

    def __init__(self, profile, region):
        self.profile = profile
        self.region  = region

    def run(self,asg_name):
        session = botocore.session.Session(profile=self.profile)
        asg = session.create_client('autoscaling',self.region)
        ec2 = session.create_client('ec2',self.region)

        groups = asg.describe_auto_scaling_groups()
        matching_groups = [g for g in groups['AutoScalingGroups'] for t in g['Tags'] if t['Key'] == 'Name' and t['Value'] == asg_name]

        groups_to_instances = {group['AutoScalingGroupName']: [instance['InstanceId'] for instance in group['Instances']] for group in matching_groups}
        instances_to_groups = {instance['InstanceId']: group['AutoScalingGroupName'] for group in matching_groups for instance in group['Instances'] }

        # We only need to check for ASGs in an ELB if we have more than 1.
        # If a cluster is running with an ASG out of the ELB, then there are larger problems.
        active_groups = defaultdict(dict)
        if len(matching_groups) > 1:
            elb = session.create_client('elb',self.region)
            for group in matching_groups:
                for load_balancer_name in group['LoadBalancerNames']:
                    instances = elb.describe_instance_health(LoadBalancerName=load_balancer_name)
                    active_instances = [instance['InstanceId'] for instance in instances['InstanceStates'] if instance['State'] == 'InService']
                    for instance_id in active_instances:
                        active_groups[instances_to_groups[instance_id]] = 1 
            if len(active_groups) > 1:
                # When we have more than a single active ASG, we need to bail out as we don't know what ASG to pick an instance from
                print("Multiple active ASGs - unable to choose an instance", file=sys.stderr)
                return
        else:
            active_groups = { g['AutoScalingGroupName']: 1 for g in matching_groups }


        for group in active_groups.keys():
            for group_instance in groups_to_instances[group]:
                instance = ec2.describe_instances(InstanceIds=[group_instance])['Reservations'][0]['Instances'][0]
                if 'PrivateIpAddress' in instance:
                    print("{},".format(instance['PrivateIpAddress']))
                    return # We only want a single IP


if __name__=="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--profile', help='The aws profile to use when connecting.')
    parser.add_argument('-l', '--list', help='Ansible passes this, we ignore it.', action='store_true', default=True)
    parser.add_argument('--asg',help='Name of the ASG we want active instances from.', required=True)
    args = parser.parse_args()

    region = environ.get('AWS_REGION','us-east-1')

    ActiveInventory(args.profile,region).run(args.asg)
