from __future__ import absolute_import
from __future__ import print_function
import argparse
import boto.ec2
from boto.utils import get_instance_metadata, get_instance_identity
from boto.exception import AWSConnectionError
import os
import subprocess
import traceback
import socket
import time

# Services that should be checked for migrations.
GENERIC_MIGRATION_COMMAND = ". {env_file}; sudo -E -u {user} {python} {code_dir}/manage.py showmigrations"
EDXAPP_MIGRATION_COMMANDS = {
        'lms':        "/edx/bin/edxapp-migrate-lms --noinput --list",
        'cms':        "/edx/bin/edxapp-migrate-cms --noinput --list",
        'workers':    "/edx/bin/edxapp-migrate-cms --noinput --list; /edx/bin/edxapp-migrate-lms --noinput --list",
    }
NGINX_ENABLE = {
        'lms': "sudo ln -sf /edx/app/nginx/sites-available/lms /etc/nginx/sites-enabled/lms",
        'cms': "sudo ln -sf /edx/app/nginx/sites-available/cms /etc/nginx/sites-enabled/cms",
    }

# Max amount of time to wait for tags to be applied.
MAX_BACKOFF = 120
INITIAL_BACKOFF = 1

REGION = get_instance_identity()['document']['region']

def services_for_instance(instance_id):
    """
    Get the list of all services named by the services tag in this
    instance's tags.
    """
    ec2 = boto.ec2.connect_to_region(REGION)
    reservations = ec2.get_all_instances(instance_ids=[instance_id])
    for reservation in reservations:
        for instance in reservation.instances:
            if instance.id == instance_id:
                try:
                    services = instance.tags['services'].split(',')
                except KeyError as ke:
                    msg = "Tag named 'services' not found on this instance({})".format(instance_id)
                    raise Exception(msg)

                for service in services:
                    yield service

def edp_for_instance(instance_id):
    ec2 = boto.ec2.connect_to_region(REGION)
    reservations = ec2.get_all_instances(instance_ids=[instance_id])
    for reservation in reservations:
        for instance in reservation.instances:
            if instance.id == instance_id:
                try:
                    environment = instance.tags['environment']
                    deployment = instance.tags['deployment']
                    play = instance.tags['play']
                except KeyError as ke:
                    msg = "{} tag not found on this instance({})".format(ke.message, instance_id)
                    raise Exception(msg)
                return (environment, deployment, play)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Enable all services that are in the services tag of this ec2 instance.")
    parser.add_argument("-a","--available",
        help="The location of the available services.")
    parser.add_argument("-e","--enabled",
        help="The location of the enabled services.")

    app_migration_args = parser.add_argument_group("app_migrations",
            "Args for running app migration checks.")
    app_migration_args.add_argument("--check-migrations", action='store_true',
        help="Enable checking migrations.")
    app_migration_args.add_argument("--check-migrations-service-names",
        help="Comma seperated list of service names that should be checked for migrations")
    app_migration_args.add_argument("--app-python",
        help="Path to python to use for executing migration check.")
    app_migration_args.add_argument("--app-env",
        help="Location of the app environment file.")
    app_migration_args.add_argument("--app-code-dir",
        help="Location of the app code.")

    args = parser.parse_args()

    report = []
    prefix = None

    instance_id = get_instance_metadata()['instance-id']
    prefix = instance_id

    ec2 = boto.ec2.connect_to_region(REGION)
    reservations = ec2.get_all_instances(instance_ids=[instance_id])
    instance = reservations[0].instances[0]
    if instance.instance_profile['arn'].endswith('/abbey'):
        print("Running an abbey build. Not starting any services.")
        # Needs to exit with 1 instead of 0 to prevent
        # services from starting.
        exit(1)
    time_left = MAX_BACKOFF
    backoff = INITIAL_BACKOFF

    environment = None
    deployment = None
    play = None
    while time_left > 0:
        try:
            environment, deployment, play = edp_for_instance(instance_id)
            prefix = "{environment}-{deployment}-{play}-{instance_id}".format(
                environment=environment,
                deployment=deployment,
                play=play,
                instance_id=instance_id)
            break
        except Exception as e:
            print(("Failed to get EDP for {}: {}".format(instance_id, str(e))))
            # With the time limit being 2 minutes we will
            # try 5 times before giving up.
            time.sleep(backoff)
            time_left -= backoff
            backoff = backoff * 2

    if environment is None or deployment is None or play is None:
        msg = "Unable to retrieve environment, deployment, or play tag."
        print(msg)
        exit(1)

    #get the hostname of the sandbox
    hostname = socket.gethostname()

    ami_id = get_instance_metadata()['ami-id']

    try:
        #get the list of the volumes, that are attached to the instance
        volumes = ec2.get_all_volumes(filters={'attachment.instance-id': instance_id})

        for volume in volumes:
            volume.add_tags({"hostname": hostname,
                             "environment": environment,
                             "deployment": deployment,
                             "cluster": play,
                             "instance-id": instance_id,
                             "ami-id": ami_id,
                             "created": volume.create_time })
    except Exception as e:
        msg = "Failed to tag volumes associated with {}: {}".format(instance_id, str(e))
        print(msg)

    try:
        for service in services_for_instance(instance_id):
            if service in NGINX_ENABLE:
                subprocess.call(NGINX_ENABLE[service], shell=True)
                report.append("Enabling nginx: {}".format(service))
            # We have to reload the new config files
            subprocess.call("/bin/systemctl reload nginx", shell=True)

            if (args.check_migrations and
                args.app_python != None and
                args.app_env != None and
                args.app_code_dir != None and
                args.check_migrations_service_names != None and
                service in args.check_migrations_service_names.split(',')):

                user = play
                # Legacy naming workaround
                # Using the play works everywhere but here.
                if user == "analyticsapi":
                    user="analytics_api"

                cmd_vars = {
                    'python': args.app_python,
                    'env_file': args.app_env,
                    'code_dir': args.app_code_dir,
                    'service': service,
                    'user': user,
                    }
                cmd = GENERIC_MIGRATION_COMMAND.format(**cmd_vars)
                if service in EDXAPP_MIGRATION_COMMANDS:
                    cmd = EDXAPP_MIGRATION_COMMANDS[service]

                if os.path.exists(cmd_vars['code_dir']):
                    os.chdir(cmd_vars['code_dir'])
                    # Run migration check command.
                    output = subprocess.check_output(cmd, shell=True, )
                    if b'[ ]' in output:
                        raise Exception("Migrations have not been run for {}".format(service))
                    else:
                        report.append("Checked migrations: {}".format(service))

            # Link to available service.
            available_file = os.path.join(args.available, "{}.conf".format(service))
            link_location = os.path.join(args.enabled, "{}.conf".format(service))
            if os.path.exists(available_file):
                subprocess.call("sudo -u supervisor ln -sf {} {}".format(available_file, link_location), shell=True)
                report.append("Enabling service: {}".format(service))
            else:
                raise Exception("No conf available for service: {}".format(link_location))

    except AWSConnectionError as ae:
        msg = "{}: ERROR : {}".format(prefix, ae)
        raise ae
    except Exception as e:
        msg = "{}: ERROR : {}".format(prefix, e)
        print(msg)
        traceback.print_exc()
        raise e
    else:
        msg = "{}: {}".format(prefix, " | ".join(report))
        print(msg)
