#!/usr/bin/env python

from argparse import ArgumentParser
import time
import boto


def await_elb_instance_state(lb, instance_id, awaited_state):
    """blocks until the ELB reports awaited_state
    for instance_id.
    lb = loadbalancer object
    instance_id : instance_id (string)
    awaited_state : state to poll for (string)"""

    start_time = time.time()
    while True:
        state = lb.get_instance_health([instance_id])[0].state
        if state == awaited_state:
            print "Load Balancer {lb} is in awaited state " \
                  "{awaited_state}, proceeding.".format(
                  lb=lb.dns_name,
                  awaited_state=awaited_state)
            break
        else:
            print "Checking again in 2 seconds. Elapsed time: {0}".format(
                time.time() - start_time)
            time.sleep(2)


def deregister():
    """Deregister the instance from all ELBs and wait for the ELB
    to report them out-of-service"""

    for lb in active_lbs:
        lb.deregister_instances([args.instance])
        await_elb_instance_state(lb, args.instance, 'OutOfService')


def register():
    """Register the instance for all ELBs and wait for the ELB
    to report them in-service"""
    for lb in active_lbs:
        lb.register_instances([args.instance])
        await_elb_instance_state(lb, args.instance, 'InService')


def parse_args():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="sp_action")
    subparsers.add_parser('register', help='register an instance')
    subparsers.add_parser('deregister', help='deregister an instance')

    parser.add_argument('-e', '--elbs', required=True,
                        help="Comma separated list of ELB names")
    parser.add_argument('-i', '--instance', required=True,
                        help="Single instance to operate on")
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    elb = boto.connect_elb()
    elbs = elb.get_all_load_balancers()
    active_lbs = sorted(
        lb
        for lb in elbs
        if lb.name in args.elbs.split(','))

    print "ELB : " + str(args.elbs.split(','))
    print "Instance: " + str(args.instance)
    if args.sp_action == 'deregister':
        print "Deregistering an instance"
        deregister()
    elif args.sp_action == 'register':
        print "Registering an instance"
        register()
