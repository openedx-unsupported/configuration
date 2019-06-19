#! /usr/bin/env python

import argparse
import boto
from boto.utils import get_instance_metadata
from boto.exception import AWSConnectionError
import os
import subprocess
import traceback
import socket
import time

# Max amount of time to wait for tags to be applied.
MAX_BACKOFF = 120
INITIAL_BACKOFF = 1

def edp_for_instance(instance_id):
    ec2 = boto.connect_ec2()
    reservations = ec2.get_all_instances(instance_ids=[instance_id])
    for reservation in reservations:
        for instance in reservation.instances:
            if instance.id == instance_id:
                try:
                    environment = instance.tags['environment']
                    deployment = instance.tags['deployment']
                    play = instance.tags['play']
                except KeyError as ke:
                    msg = "{} tag not found on this instance({})".format(ke.message, instance_id)
                    raise Exception(msg)
                return (environment, deployment, play)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Get Instance role (EDP)")

    args = parser.parse_args()
    time_left = MAX_BACKOFF
    backoff = INITIAL_BACKOFF
    instance_id = get_instance_metadata()['instance-id']
    ec2 = boto.connect_ec2()
    environment = None
    deployment = None
    play = None
    while time_left > 0:
	    try:
		environment, deployment, play = edp_for_instance(instance_id)
		prefix = "{environment}-{deployment}-{play}-{instance_id}".format(
		    environment=environment,
		    deployment=deployment,
		    play=play,
		    instance_id=instance_id)
		break
	    except:
		# With the time limit being 2 minutes we will
		# try 5 times before giving up.
		time.sleep(backoff)
		time_left -= backoff
		backoff = backoff * 2

    if environment is None or deployment is None or play is None:
        msg = "Unable to retrieve environment, deployment, or play tag."
        print(msg)
        exit(1)

    print("{}_{}_{}".format(environment, deployment, play))
    exit(0)

