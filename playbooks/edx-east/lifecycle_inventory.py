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
import argparse
import boto
import json
from collections import defaultdict

class LifecycleInventory():

    profile = None

    def __init__(self, profile):
        parser = argparse.ArgumentParser()
        self.profile = profile

    def get_e_d_from_tags(self, group):

        environment = "default_environment"
        deployment = "default_deployment"

        for r in group.tags:
            if r.key == "environment":
                environment = r.value
            elif r.key == "deployment":
                deployment = r.value
        return environment,deployment

    def get_instance_dict(self):
        ec2 = boto.connect_ec2(profile_name=self.profile)
        reservations = ec2.get_all_instances()

        dict = {}

        for instance in [i for r in reservations for i in r.instances]:
            dict[instance.id] = instance

        return dict

    def run(self):
        autoscale = boto.connect_autoscale(profile_name=self.profile)
        groups = autoscale.get_all_groups()

        instances = self.get_instance_dict()
        inventory = defaultdict(list)

        for group in groups:

            for instance in group.instances:

                private_ip_address = instances[instance.instance_id].private_ip_address
                if private_ip_address:
                    environment,deployment = self.get_e_d_from_tags(group)
                    inventory[environment + "_" + deployment + "_" + instance.lifecycle_state.replace(":","_")].append(private_ip_address)
                    inventory[group.name].append(private_ip_address)
                    inventory[group.name + "_" + instance.lifecycle_state.replace(":","_")].append(private_ip_address)
                    inventory[instance.lifecycle_state.replace(":","_")].append(private_ip_address)

        print json.dumps(inventory, sort_keys=True, indent=2)

if __name__=="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--profile', help='The aws profile to use when connecting.')
    parser.add_argument('-l', '--list', help='Ansible passes this, we ignore it.', action='store_true', default=True)
    args = parser.parse_args()

    LifecycleInventory(args.profile).run()



