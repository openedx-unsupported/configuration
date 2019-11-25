#!/usr/bin/env python

"""
Build an ansible inventory based on autoscaling group instance lifecycle state.

Outputs JSON to stdout with keys for each state and combination of autoscaling
group and state.

{
  "InService": [
    "10.0.47.127",
    "10.0.46.174"
  ],
  "Terminating:Wait": [
    "10.0.48.104"
  ],
  "e-d-CommonClusterServerAsGroup": [
    "10.0.47.127",
    "10.0.46.174"
  ],
  "e-d-CommonClusterServerAsGroup_InService": [
    "10.0.47.127",
    "10.0.46.174"
  ],
  "e-d-CommonClusterServerAsGroup_InService": [
    "10.0.48.104"
  ]

}
"""
from __future__ import absolute_import
from __future__ import print_function
import argparse
import boto3
import json
from collections import defaultdict
from os import environ

class LifecycleInventory():

    def __init__(self, region):
        parser = argparse.ArgumentParser()
        self.region = region

    def get_e_d_from_tags(self, group):

        environment = "default_environment"
        deployment = "default_deployment"

        for r in group['Tags']:
            if r['Key'] == "environment":
                environment = r['Value']
            elif r['Key'] == "deployment":
                deployment = r['Value']
        return environment,deployment

    def get_instance_dict(self):
        ec2 = boto3.client('ec2', region_name=self.region)
        reservations = ec2.describe_instances()['Reservations']

        dict = {}

        for instance in [i for r in reservations for i in r['Instances']]:
            dict[instance['InstanceId']] = instance

        return dict

    def get_asgs(self):
        asg = boto3.client('autoscaling', region_name=self.region)
        asg_request = asg.describe_auto_scaling_groups()
        asg_accumulator = asg_request['AutoScalingGroups']

        while 'NextToken' in asg_request:
            asg_request = asg.describe_auto_scaling_groups(NextToken=asg_request['NextToken'])
            asg_accumulator.extend(asg_request['AutoScalingGroups'])

        return asg_accumulator

    def run(self):

        groups = self.get_asgs()

        instances = self.get_instance_dict()
        inventory = defaultdict(list)

        for group in groups:

            for instance in group['Instances']:

                private_ip_address = instances[instance['InstanceId']]['PrivateIpAddress']
                if private_ip_address:
                    environment,deployment = self.get_e_d_from_tags(group)
                    inventory[environment + "_" + deployment + "_" + instance['LifecycleState'].replace(":","_")].append(private_ip_address)
                    inventory[group['AutoScalingGroupName']].append(private_ip_address)
                    inventory[group['AutoScalingGroupName'] + "_" + instance['LifecycleState'].replace(":","_")].append(private_ip_address)
                    inventory[instance['LifecycleState'].replace(":","_")].append(private_ip_address)

        print(json.dumps(inventory, sort_keys=True, indent=2))

if __name__=="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--region', help='The aws region to use when connecting.', default=environ.get('AWS_REGION', 'us-east-1'))
    parser.add_argument('-l', '--list', help='Ansible passes this, we ignore it.', action='store_true', default=True)
    args = parser.parse_args()


    LifecycleInventory(args.region).run()
