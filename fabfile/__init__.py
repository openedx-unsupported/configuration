# Additional Tasks
import cache
import clean
import ec2
import audit
import git
import hosts
import locks
import os
import ssh
import status
import migrate_check

import yaml
from dogapi import dog_stats_api, dog_http_api
from timestamps import TSWrapper

# Global tasks
import logging
from fabric.api import env, task, runs_once
from output import squelch
from datetime import datetime
import sys
import time
from fabric.api import execute, local, task, runs_once
from fabric.utils import fastprint
from fabric.colors import blue
from ssh_tunnel import setup_tunnel

# These imports are to give aliases for these tasks
from hosts import by_tags as tag
from hosts import by_tags as tags
from hosts import exemplar_from_tags as exemplar
from git import default_deploy as deploy

env.linewise = True
env.noop = False
env.use_ssh_config = True

FORMAT = '[ %(asctime)s ] : %(message)s'
logging.basicConfig(format=FORMAT, level=logging.WARNING)

# add timestamps to output
sys.stdout = TSWrapper(sys.stdout)
sys.stderr = TSWrapper(sys.stderr)

path = os.path.abspath(__file__)
with open(os.path.join(
        os.path.dirname(path), '../package_data.yaml')) as f:
    package_data = yaml.load(f)
    dog_stats_api.start(api_key=package_data['datadog_api'], statsd=True)
    dog_http_api.api_key = package_data['datadog_api']


@task
def noop():
    """
    Disable modification of servers
    """
    env.noop = True
    dog_stats_api.stop()


@task
def quiet():
    """
    Disables verbose output
    """
    squelch()


@runs_once
@task()
def log(fname=None):
    """
    Writes a logfile to disk of the run
    """

    if not fname:
        d = datetime.now()
        fname = d.strftime('/var/tmp/fab-%Y%m%d-%H%M%S-{0}.log'.format(
            os.getpid()))

    env.logfile = fname
    sys.stdout.log_to_file(fname)
    sys.stderr.log_to_file(fname)
