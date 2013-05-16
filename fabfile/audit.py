import logging
from fabric.api import serial, task, parallel, env, execute, runs_once, settings,sudo
from fabfile.safety import noopable
from multiprocessing import Manager
from timestamps import no_ts
from packages import PackageInfo
import tempfile
from output import notify


@task
@parallel
def collect_installed_packages(results):
    """
    Collect all installed packages for the selected hosts and store them in env
    """
    print env.host
    pkg_info = PackageInfo()
    results[env.host] = pkg_info.installed_packages()


@task
@serial
def display_installed_packages(installed_packages):
    """
    Print all installed packages collected by collect_installed_packages
    """

    # FIXME: env.hosts loses the port information here, not sure why
    with no_ts():
        for pkg in installed_packages['{0}:22'.format(env.host)]:
            notify("{pkg.name} = {pkg.revision}".format(pkg=pkg))


@task(default=True)
@runs_once
def installed_packages(from_links=False):
    """
    List all of the installed packages on the selected packages
    """
    installed_packages = Manager().dict()
    execute(collect_installed_packages, installed_packages)
    execute(display_installed_packages, installed_packages)


@task
def audit_user(user, audit_output=None):
    """
    Logs on provided hosts and runs id for the supplied user with sudo.  Output
    is logged to the provided file argument or a default using the
    python gettempdir() function and the following file name format:

    /tmp/audit-user-{user}.csv

    The contents of this file are

    host,user,command output

    Note that if the file already exists, output will be appended to the
    existing file.

    """
    logging.info("Auditing {host}.".format(host=env.host_string))

    if not audit_output:
        audit_output = tempfile.gettempdir() + "/audit-user-{user}.csv".format(
            user=user)

    with settings(warn_only=True):
        with open(audit_output, 'a') as audit:
            output = noopable(sudo)("id {user}".format(user=user))
            audit.write("{host},{user},{output}\n".format(
                host=env.host_string,
                user=user,
                output=output
                )
        )

@task
def remove_user(user):
    """
    Logs on to provided hosts and runs userdel for the supplied user with sudo.
    The user's home directory is preserved.
    """

    logging.info("Removing {user} user from {host}.".format(
        user=user,host=env.host_string))

    with settings(warn_only=True):
        output = noopable(sudo)("userdel {user}".format(user=user))
        logging.info("Output of userdel command on host {host} was {out}".format(
            host=env.host_string,out=output
            )
        )

