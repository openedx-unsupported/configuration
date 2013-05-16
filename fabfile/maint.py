from fabric.api import task, parallel, put, sudo
from safety import noopable
from .modifiers import rolling
from StringIO import StringIO
import json

__all__ = ['on', 'off','maintain_service','unmaintain_service']

services = ['lms','cms','lms-xml','lms-preview']


def set_maintenance(value):
    noopable(put)(StringIO(json.dumps({'maintenance': value})), '/etc/facter/facts.d/mitx_maintenance.json', use_sudo=True)


@task
@parallel
def on():
    """
    Enable maintenance mode
    """
    set_maintenance(True)
    puppet.checkin('maintenance')


@task
@parallel
def off():
    """
    Disable maintenance mode
    """
    set_maintenance(False)
    puppet.checkin('maintenance')


@task
@rolling
def maintain_service(service):
    """
    Puts a specified edxapp service into maintenance mode by replacing
    its nginx sites-enabled link with a link to the maintenance vhost.
    """

    if service not in services:
        raise Exception("Provided service not in the service inventory. "
                        "Acceptable values are {services}".format(
            services=services
        ))

    noopable(sudo)("rm -f /etc/nginx/sites-enabled/{service}".format(
        service=service))

    noopable(sudo)("ln -s /etc/nginx/sites-available/{service}-maintenance"
                   " /etc/nginx/sites-enabled/{service}-maintenance".format(
        service=service))

    noopable(sudo)("service nginx reload")

@task
@rolling
def unmaintain_service(service):
    """
    Removes a specified edxapp service from maintenance mode by replacing
    the appropriate link in /etc/nginx/sites-enabled.
    """

    if service not in services:
        raise Exception("Provided service not in the service inventory. "
                        "Acceptable values are {services}".format(
            services=services
        ))

    noopable(sudo)("rm -f /etc/nginx/sites-enabled/{service}-maintenance".format(
        service=service))

    noopable(sudo)("ln -s /etc/nginx/sites-available/{service}"
                   " /etc/nginx/sites-enabled/{service}".format(
        service=service))

    noopable(sudo)("service nginx reload")
