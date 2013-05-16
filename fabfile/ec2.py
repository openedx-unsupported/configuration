import boto
from fabric.api import run, task, parallel, env

env.instance_ids = {}


def instance_id():
    if env.host_string not in env.instance_ids:
        env.instance_ids[env.host_string] = run('wget -q -O - http://169.254.169.254/latest/meta-data/instance-id')

    return env.instance_ids[env.host_string]
