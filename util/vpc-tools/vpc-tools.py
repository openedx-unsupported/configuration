"""VPC Tools.

Usage:
    vpc-tools.py ssh-config (vpc <vpc_id> | stack-name <stack_name>) [(identity-file <identity_file>)] user <user> [(config-file <config_file>)] [(strict-host-check <strict_host_check>)] [(jump-box <jump_box>)]
    vpc-tools.py (-h --help)
    vpc-tools.py (-v --version)

Options:
    -h --help       Show this screen.
    -v --version    Show version.

"""
import boto
from docopt import docopt
from vpcutil import vpc_for_stack_name
from vpcutil import stack_name_for_vpc
from collections import defaultdict


VERSION="vpc tools 0.1"
DEFAULT_USER="ubuntu"
DEFAULT_HOST_CHECK="ask"

BASTION_CONFIG = """Host {jump_box}
    HostName {ip}
    ForwardAgent yes
    User {user}
    StrictHostKeyChecking {strict_host_check}
    {identity_line}
    """

HOST_CONFIG = """# Instance ID: {instance_id}
Host {name}
    ProxyCommand ssh -q {config_file} -W %h:%p {jump_box}
    HostName {ip}
    ForwardAgent yes
    User {user}
    StrictHostKeyChecking {strict_host_check}
    {identity_line}
    """

DIRECT_HOST_CONFIG = """# Instance ID: {instance_id}
Host {name}
    HostName {ip}
    ForwardAgent yes
    User {user}
    StrictHostKeyChecking {strict_host_check}
    {identity_line}
    """


BASTION_HOST_CONFIG = """# Instance ID: {instance_id}
Host {name}
    HostName {ip}
    ForwardAgent yes
    User {user}
    StrictHostKeyChecking {strict_host_check}
    {identity_line}
    """



def dispatch(args):

    if args.get("ssh-config"):
        _ssh_config(args)

def _ssh_config(args):
    if args.get("vpc"):
      vpc_id = args.get("<vpc_id>")
      stack_name = stack_name_for_vpc(vpc_id)
    elif args.get("stack-name"):
      stack_name = args.get("<stack_name>")
      vpc_id = vpc_for_stack_name(stack_name)
    else:
      raise Exception("No vpc_id or stack_name provided.")

    vpc = boto.connect_vpc()

    identity_file = args.get("<identity_file>", None)
    if identity_file:
        identity_line = "IdentityFile {}".format(identity_file)
    else:
        identity_line = ""

    user = args.get("<user>")
    config_file = args.get("<config_file>")
    strict_host_check = args.get("<strict_host_check>")

    if not user:
      user = DEFAULT_USER

    if not strict_host_check:
      strict_host_check = DEFAULT_HOST_CHECK

    if config_file:
      config_file = "-F {}".format(config_file)
    else:
      config_file = ""

    if args.get("jump-box"):
        jump_box = args.get("<jump_box>")
    else:
        jump_box = "{stack_name}-bastion".format(stack_name=stack_name)

    friendly = "{stack_name}-{logical_id}-{instance_number}"
    id_type_counter = defaultdict(int)

    reservations = vpc.get_all_instances(filters={'vpc-id' : vpc_id})

    for reservation in reservations:
        for instance in reservation.instances:

            if 'play' in instance.tags:
                logical_id = instance.tags['play']
            elif 'role' in instance.tags:
                # deprecated, use "play" instead
                logical_id = instance.tags['role']
            elif 'group' in instance.tags:
                logical_id = instance.tags['group']
            elif 'aws:cloudformation:logical-id' in instance.tags:
                logical_id = instance.tags['aws:cloudformation:logical-id']
            else:
                continue
            instance_number = id_type_counter[logical_id]
            id_type_counter[logical_id] += 1

            if logical_id == "BastionHost" or logical_id == 'bastion':

                print BASTION_CONFIG.format(
                    jump_box=jump_box,
                    ip=instance.ip_address,
                    user=user,
                    strict_host_check=strict_host_check,
                    identity_line=identity_line)

                print BASTION_HOST_CONFIG.format(
                    name=instance.private_ip_address,
                    ip=instance.ip_address,
                    user=user,
                    instance_id=instance.id,
                    strict_host_check=strict_host_check,
                    identity_line=identity_line)

                #duplicating for convenience with ansible
                name = friendly.format(stack_name=stack_name,
                                       logical_id=logical_id,
                                       instance_number=instance_number)

                print BASTION_HOST_CONFIG.format(
                    name=name,
                    ip=instance.ip_address,
                    user=user,
                    strict_host_check=strict_host_check,
                    instance_id=instance.id,
                    identity_line=identity_line)

            else:
                # Print host config even for the bastion box because that is how
                # ansible accesses it.
                if jump_box == "none":
                    print DIRECT_HOST_CONFIG.format(
                        name=instance.private_ip_address,
                        ip=instance.private_ip_address,
                        user=user,
                        config_file=config_file,
                        strict_host_check=strict_host_check,
                        instance_id=instance.id,
                        identity_line=identity_line)

                    #duplicating for convenience with ansible
                    name = friendly.format(stack_name=stack_name,
                                           logical_id=logical_id,
                                           instance_number=instance_number)

                    print DIRECT_HOST_CONFIG.format(
                        name=name,
                        ip=instance.private_ip_address,
                        user=user,
                        config_file=config_file,
                        strict_host_check=strict_host_check,
                        instance_id=instance.id,
                        identity_line=identity_line)

                else:
                    print HOST_CONFIG.format(
                        name=instance.private_ip_address,
                        jump_box=jump_box,
                        ip=instance.private_ip_address,
                        user=user,
                        config_file=config_file,
                        strict_host_check=strict_host_check,
                        instance_id=instance.id,
                        identity_line=identity_line)

                    #duplicating for convenience with ansible
                    name = friendly.format(stack_name=stack_name,
                                           logical_id=logical_id,
                                           instance_number=instance_number)

                    print HOST_CONFIG.format(
                        name=name,
                        jump_box=jump_box,
                        ip=instance.private_ip_address,
                        user=user,
                        config_file=config_file,
                        strict_host_check=strict_host_check,
                        instance_id=instance.id,
                        identity_line=identity_line)

if __name__ == '__main__':
    args = docopt(__doc__, version=VERSION)
    dispatch(args)
