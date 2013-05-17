from fabric.api import task, env, abort
from fabric.colors import red
import os
import re


@task(default=True)
def ssh(user=None):

    if user is None:
        user = env.user
    if len(env.hosts) != 1:
        abort(red('Please specify one host for ssh'))

    for host in env.hosts:
        host = re.sub(':(\d+)', r' -p\1 ', host)
        os.system('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -l {0} {1}'.format(user, host))
