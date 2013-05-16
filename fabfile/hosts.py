import boto
from fabric.decorators import serial
from ssh_tunnel import setup_tunnel
import socket
from fabric.api import env, task, abort
from fabric.colors import red
import logging


def hosts_by_tag(tag, value):
    """
    Return a list of all hosts that have the specified value for the specified
    tag
    """
    return hosts_by_tags(**{tag: value})


def hosts_by_tags(**tags):
    """
    Return a list of all hosts that have the specified value for the specified
    tags.

    Tag values are allowed to include wildcards

    If no variant tag is specified, this command will ignore all hosts
    that have a variant specified.
    """

    if 'env' in tags:
        tags['environment'] = tags['env']
        del(tags['env'])

    ec2 = boto.connect_ec2()
    hosts = []
    for res in ec2.get_all_instances(filters={'tag:' + tag: value
                                        for tag, value in tags.iteritems()
                                        if value != '*'}):
        for inst in res.instances:
            if inst.state == "running":
                if (inst.public_dns_name):
                    hosts.append(inst.public_dns_name)
                else:
                    hosts.append(inst.private_dns_name)
    print hosts
    return hosts

def _fleet():
    ec2 = boto.connect_ec2()
    hosts = []
    for res in ec2.get_all_instances():
        for inst in res.instances:
            if inst.state == "running":
                try:
                    instance_name = inst.tags['Name']
                except:
                    logging.warning("Instance with id {id} and {dns} has no assigned Name.".format(id=inst.id,dns=inst.public_dns_name))


                host_to_add = instance_name + "." + DOMAIN

                # fallback to the public hostname if the m.edx.org
                # name doesn't exist
                try:
                    socket.gethostbyname(host_to_add.replace(':22',''))
                except socket.error:
                    if inst.public_dns_name:
                        host_to_add = inst.public_dns_name

                if host_to_add:
                    hosts.append(host_to_add)
    return hosts


def exemplar(**tags):
    """
    Return the hostname of one host from the specified set
    of tags, or None if there is no such host
    """

    hosts = hosts_by_tags(**tags)
    if hosts:
        return hosts[0]
    else:
        return None

@task(alias='exemplar')
def exemplar_from_tags(**tags):
    env.hosts.append(exemplar(**tags))


@task(aliases=['tag', 'tags'])
def by_tags(**tags):
    """
    Add all running hosts that match the tag names provided
    as keyword arguments.

    """

    env.hosts.extend(hosts_by_tags(**tags))
    env.hosts.sort()
    env.hosts = setup_tunnel(env.hosts)


@task(aliases=['fleet'])
def fleet():
    """
    Return a list of all hosts available  and running via the default AWS
    credentials.

    Your ability to operate on these hosts will depend upon the ssh credentials
    that you are using to drive fab.  There is likely to be a mismatch between
    what hosts you can see via IAM managed AWS credentials and which hosts
    you can actually connect to even if you are using highly privileged
    AWS pems.
    """
    hosts = _fleet()
    env.hosts.extend(hosts)
    env.hosts.sort()
    env.hosts = setup_tunnel(env.hosts)
