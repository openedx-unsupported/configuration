"""VPC Tools.

Usage:
    vpc-tools.py ssh-config vpc <vpc_id> identity-file <identity_file> user <user>
    vpc-tools.py (-h --help)
    vpc-tools.py (-v --version)

Options:
    -h --help       Show this screen.
    -v --version    Show version.

"""
import boto
from docopt import docopt


VERSION="vpc tools 0.1"
DEFAULT_USER="ubuntu"

JUMPBOX_CONFIG = """
    Host {jump_box}
      HostName {ip}
      IdentityFile {identity_file}
      ForwardAgent yes
      User {user}
    """

HOST_CONFIG = """
    Host {name}
      ProxyCommand ssh -W %h:%p {jump_box}
      HostName {ip}
      IdentityFile {identity_file}
      ForwardAgent yes
      User {user}
    """


def dispatch(args):

    if args.get("ssh-config"):
        _ssh_config(args)

def _ssh_config(args):

    vpc = boto.connect_vpc()

    identity_file = args.get("<identity_file>")
    user = args.get("<user>",DEFAULT_USER)
    vpc_id = args.get("<vpc_id>")

    jump_box = "{vpc_id}-jumpbox".format(vpc_id=vpc_id)
    friendly = "{vpc_id}-{logical_id}-{instance_id}"

    reservations = vpc.get_all_instances(filters={'vpc-id' : vpc_id})

    for reservation in reservations:
        for instance in reservation.instances:

            logical_id = instance.__dict__['tags']['aws:cloudformation:logical-id']

            if logical_id == "BastionHost":

                print JUMPBOX_CONFIG.format(
                    jump_box=jump_box,
                    ip=instance.ip_address,
                    user=user,
                    identity_file=identity_file)

            else:
                print HOST_CONFIG.format(
                    name=instance.private_ip_address,
                    vpc_id=vpc_id,
                    jump_box=jump_box,
                    ip=instance.private_ip_address,
                    user=user,
                    logical_id=logical_id,
                    identity_file=identity_file)

            #duplicating for convenience with ansible
            name = friendly.format(vpc_id=vpc_id,
                                   logical_id=logical_id,
                                   instance_id=instance.id)
            print HOST_CONFIG.format(
                name=name,
                vpc_id=vpc_id,
                jump_box=jump_box,
                ip=instance.private_ip_address,
                user=user,
                logical_id=logical_id,
                identity_file=identity_file)


if __name__ == '__main__':
    args = docopt(__doc__, version=VERSION)
    dispatch(args)