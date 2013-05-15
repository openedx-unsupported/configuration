import os
import socket
import time

from output import notify
from safety import noopable
from fabric.api import task, run, env, settings, sudo, abort
from fabric.api import runs_once, execute, serial, hide

MAX_SLEEP_TIME = 10

LOCK_FILE = '/opt/deploy/.lock'


@task
@runs_once
def wait_for_all_locks():
    execute('locks.wait_for_lock', hosts=sorted(env.hosts))


@task
@runs_once
def remove_all_locks():
    execute('locks.remove_lock', hosts=sorted(env.hosts, reverse=True))


@task
@serial
def remove_lock():
    noopable(sudo)("test ! -f {0} || rm {0}".format(LOCK_FILE))


@task
@serial
def wait_for_lock():
    if hasattr(env, 'deploy_user'):
        lock_user = env.deploy_user
    else:
        lock_user = env.user

    LOCK_ID = 'u:{user} h:{host} pid:{pid}'.format(user=lock_user,
                                    host=socket.gethostname(),
                                pid=str(os.getpid()))
    sleep_time = 0.1
    timeout = 120
    start_time = time.time()

    with settings(warn_only=True):
        while True:
            wait_time = time.time() - start_time

            # break if the lockfile is removed or if it belongs to this pid
            # if it exists lock_status will have the file's contents

            with hide('running', 'stdout', 'stderr', 'warnings'):
                lock_status = run("test ! -f {lfile} || "
                                  "(cat {lfile} && "
                                  'grep -q "{lid}" {lfile})'.format(
                                      lfile=LOCK_FILE,
                                      lid=LOCK_ID))

                if lock_status.succeeded:
                    noopable(sudo)('echo "{0}" > {1}'.format(
                        LOCK_ID, LOCK_FILE))
                    notify("Took lock")
                    break

                elif wait_time >= timeout:
                    abort("Timeout expired, giving up")

                lock_create_time = run("stat -c %Y {0}".format(LOCK_FILE))

            delta = time.time() - float(lock_create_time)
            (dhour, dsec) = divmod(delta, 3600)

            notify("""

        !! Deploy lockfile already exists ({lockfile}) !!
            Waiting: {wait}s
            Lockfile info: [ {owner} ]
            Lock created: {dhour}h{dmin}m ago
            """.format(
                        lockfile=LOCK_FILE,
                        wait=int(timeout - wait_time),
                        owner=lock_status,
                        dhour=int(dhour),
                        dmin=int(dsec / 60),
                        ))
            time.sleep(sleep_time)
            sleep_time *= 2
            if sleep_time > MAX_SLEEP_TIME:
                sleep_time = MAX_SLEEP_TIME
