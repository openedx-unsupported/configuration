import boto
import time

from collections import namedtuple
from fabric.api import task, execute, serial
from functools import wraps, partial
from safety import noopable
from output import notify
from dogapi import dog_stats_api
from .metrics import instance_tags
from .ec2 import instance_id

MAX_SLEEP_TIME = 1


LockedElb = namedtuple('LockedElb', 'name elb lock')


def await_elb_instance_state(lb, instance_id, awaited_state):

    sleep_time = 0.1
    start_time = time.time()
    while True:
        state = lb.get_instance_health([instance_id])[0].state
        if state == awaited_state:
            notify("Load Balancer {lb} is in awaited state {awaited_state}, proceeding.".format(
                lb=lb.dns_name,
                awaited_state=awaited_state
            ))
            break
        else:

            notify("Checking again in {0} seconds. Elapsed time: {1}".format(sleep_time, time.time() - start_time))
            time.sleep(sleep_time)
            sleep_time *= 2
            if sleep_time > MAX_SLEEP_TIME:
                sleep_time = MAX_SLEEP_TIME


def rolling(func):

    @task
    @serial
    @wraps(func)
    def wrapper(*args, **kwargs):
        elb = boto.connect_elb()

        elbs = elb.get_all_load_balancers()
        execute('locks.wait_for_all_locks')

        inst_id = instance_id()
        tags = ['task:' + func.__name__] + instance_tags(inst_id)
        active_lbs = sorted(
            lb
            for lb in elbs
            if inst_id in [info.id for info in lb.instances]
        )

        timer = partial(dog_stats_api.timer, tags=tags)

        # Remove this node from the LB
        for lb in active_lbs:
            notify("Removing {id} from {lb}".format(id=inst_id, lb=lb))

            with timer('rolling.deregister_instance'):
                noopable(lb.deregister_instances)([inst_id])
                noopable(await_elb_instance_state)(lb, inst_id, "OutOfService")

        # Execute the operation
        func(*args, **kwargs)

        # Add this node back to the LBs
        for lb in active_lbs:
            notify("Adding {id} to {lb}".format(id=inst_id, lb=lb))
            with timer('rolling.register_instance'):
                noopable(lb.register_instances)([inst_id])

        with timer('rolling.wait_for_start'):
            # Wait for the node to come online in the LBs
            for lb in active_lbs:
                noopable(await_elb_instance_state)(lb, inst_id, "InService")

    return wrapper
