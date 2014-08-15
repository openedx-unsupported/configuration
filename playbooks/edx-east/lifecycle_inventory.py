#!/usr/bin/env python

import argparse
import boto
import json

class LifecycleInventory():

    profile = None

    def __init__(self):
        parser = argparse.ArgumentParser()
        group = parser.add_argument_group()
        group.add_argument('-p', '--profile', help='The aws profile to use when connecting.')
        args = parser.parse_args()

        self.profile = args.profile
        self.run()

    def push(self, the_dict, key, element):
        if key in the_dict:
            the_dict[key].append(element);
        else:
            the_dict[key] = [element]


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
        inventory = {}

        for group in groups:

            for instance in group.instances:

                private_ip_address = instances[instance.instance_id].private_ip_address

                self.push(inventory, group.name, private_ip_address)
                self.push(inventory,group.name + "_" + instance.lifecycle_state,private_ip_address)
                self.push(inventory,instance.lifecycle_state,private_ip_address)


        print json.dumps(inventory, sort_keys=True, indent=2)

LifecycleInventory()
