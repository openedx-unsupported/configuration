import argparse
import boto.ec2
from boto.utils import get_instance_metadata, get_instance_identity
from boto.exception import AWSConnectionError
import hipchat
import os
import subprocess
import traceback
import socket
import time

# Services that should be checked for migrations.
MIGRATION_COMMANDS = {
        'lms':     "/edx/bin/edxapp-migrate-lms --noinput --list",
        'cms':     "/edx/bin/edxapp-migrate-cms --noinput --list",
        'xqueue':  "SERVICE_VARIANT=xqueue sudo -E -u xqueue {python} {code_dir}/manage.py migrate --noinput --list --settings=xqueue.aws_settings",
        'ecommerce':     ". {env_file}; sudo -E -u ecommerce {python} {code_dir}/manage.py showmigrations",
        'insights':      ". {env_file}; sudo -E -u insights {python} {code_dir}/manage.py showmigrations",
        'analytics_api': ". {env_file}; sudo -E -u analytics_api {python} {code_dir}/manage.py showmigrations",
        'credentials':   ". {env_file}; sudo -E -u credentials {python} {code_dir}/manage.py showmigrations",
        'discovery':     ". {env_file}; sudo -E -u discovery {python} {code_dir}/manage.py showmigrations",
    }
HIPCHAT_USER = "PreSupervisor"

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

    migration_args = parser.add_argument_group("edxapp_migrations",
            "Args for running edxapp migration checks.")
    migration_args.add_argument("--edxapp-code-dir",
            help="Location of the edx-platform code.")
    migration_args.add_argument("--edxapp-python",
            help="Path to python to use for executing migration check.")
    migration_args.add_argument("--edxapp-env",
            help="Location of the ecommerce environment file.")

    xq_migration_args = parser.add_argument_group("xqueue_migrations",
            "Args for running xqueue migration checks.")
    xq_migration_args.add_argument("--xqueue-code-dir",
            help="Location of the xqueue code.")
    xq_migration_args.add_argument("--xqueue-python",
            help="Path to python to use for executing migration check.")

    ecom_migration_args = parser.add_argument_group("ecommerce_migrations",
            "Args for running ecommerce migration checks.")
    ecom_migration_args.add_argument("--ecommerce-python",
        help="Path to python to use for executing migration check.")
    ecom_migration_args.add_argument("--ecommerce-env",
        help="Location of the ecommerce environment file.")
    ecom_migration_args.add_argument("--ecommerce-code-dir",
        help="Location of the ecommerce code.")

    credentials_migration_args = parser.add_argument_group("credentials_migrations",
            "Args for running credentials migration checks.")
    credentials_migration_args.add_argument("--credentials-python",
        help="Path to python to use for executing migration check.")
    credentials_migration_args.add_argument("--credentials-env",
        help="Location of the credentials environment file.")
    credentials_migration_args.add_argument("--credentials-code-dir",
        help="Location of the credentials code.")

    discovery_migration_args = parser.add_argument_group("discovery_migrations",
            "Args for running discovery migration checks.")
    discovery_migration_args.add_argument("--discovery-python",
        help="Path to python to use for executing migration check.")
    discovery_migration_args.add_argument("--discovery-env",
        help="Location of the discovery environment file.")
    discovery_migration_args.add_argument("--discovery-code-dir",
        help="Location of the discovery code.")

    insights_migration_args = parser.add_argument_group("insights_migrations",
            "Args for running insights migration checks.")
    insights_migration_args.add_argument("--insights-python",
        help="Path to python to use for executing migration check.")
    insights_migration_args.add_argument("--insights-env",
        help="Location of the insights environment file.")
    insights_migration_args.add_argument("--insights-code-dir",
        help="Location of the insights code.")

    analyticsapi_migration_args = parser.add_argument_group("analytics_api_migrations",
            "Args for running analytics_api migration checks.")
    analyticsapi_migration_args.add_argument("--analytics-api-python",
        help="Path to python to use for executing migration check.")
    analyticsapi_migration_args.add_argument("--analytics-api-env",
        help="Location of the analytics_api environment file.")
    analyticsapi_migration_args.add_argument("--analytics-api-code-dir",
        help="Location of the analytics_api code.")

    hipchat_args = parser.add_argument_group("hipchat",
            "Args for hipchat notification.")
    hipchat_args.add_argument("-c","--hipchat-api-key",
        help="Hipchat token if you want to receive notifications via hipchat.")
    hipchat_args.add_argument("-r","--hipchat-room",
        help="Room to send messages to.")

    args = parser.parse_args()

    report = []
    prefix = None
    notify = None

    try:
        if args.hipchat_api_key:
            hc = hipchat.HipChat(token=args.hipchat_api_key)
            notify = lambda message: hc.message_room(room_id=args.hipchat_room,
                message_from=HIPCHAT_USER, message=message)
    except Exception as e:
        print("Failed to initialize hipchat, {}".format(e))
        traceback.print_exc()

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
            print("Failed to get EDP for {}: {}".format(instance_id, str(e)))
            # With the time limit being 2 minutes we will
            # try 5 times before giving up.
            time.sleep(backoff)
            time_left -= backoff
            backoff = backoff * 2

    if environment is None or deployment is None or play is None:
        msg = "Unable to retrieve environment, deployment, or play tag."
        print(msg)
        if notify:
            notify("{} : {}".format(prefix, msg))
        exit(0)

    #get the hostname of the sandbox
    hostname = socket.gethostname()

    try:
        #get the list of the volumes, that are attached to the instance
        volumes = ec2.get_all_volumes(filters={'attachment.instance-id': instance_id})

        for volume in volumes:
            volume.add_tags({"hostname": hostname,
                             "environment": environment,
                             "deployment": deployment,
                             "cluster": play,
                             "instance-id": instance_id,
                             "created": volume.create_time })
    except Exception as e:
        msg = "Failed to tag volumes associated with {}: {}".format(instance_id, str(e))
        print(msg)
        if notify:
            notify(msg)

    try:
        for service in services_for_instance(instance_id):
            if service in MIGRATION_COMMANDS:
                # Do extra migration related stuff.
                if service == 'xqueue' and args.xqueue_code_dir:
                    cmd = MIGRATION_COMMANDS[service].format(python=args.xqueue_python,
                        code_dir=args.xqueue_code_dir)
                    if os.path.exists(args.xqueue_code_dir):
                        os.chdir(args.xqueue_code_dir)
                        # Run migration check command.
                        output = subprocess.check_output(cmd, shell=True)
                        if 'Migrating' in output:
                            raise Exception("Migrations have not been run for {}".format(service))
                else:
                    services = {
                        "lms": {'python': args.edxapp_python, 'env_file': args.edxapp_env, 'code_dir': args.edxapp_code_dir},
                        "cms": {'python': args.edxapp_python, 'env_file': args.edxapp_env, 'code_dir': args.edxapp_code_dir},
                        "ecommerce": {'python': args.ecommerce_python, 'env_file': args.ecommerce_env, 'code_dir': args.ecommerce_code_dir},
                        "credentials": {'python': args.credentials_python, 'env_file': args.credentials_env, 'code_dir': args.credentials_code_dir},
                        "discovery": {'python': args.discovery_python, 'env_file': args.discovery_env, 'code_dir': args.discovery_code_dir},
                        "insights": {'python': args.insights_python, 'env_file': args.insights_env, 'code_dir': args.insights_code_dir},
                        "analytics_api": {'python': args.analytics_api_python, 'env_file': args.analytics_api_env, 'code_dir': args.analytics_api_code_dir}
                    }

                    if service in services and all(arg!=None for arg in services[service].values()) and service in MIGRATION_COMMANDS:
                        serv_vars = services[service]

                        cmd = MIGRATION_COMMANDS[service].format(**serv_vars)
                        if os.path.exists(serv_vars['code_dir']):
                            os.chdir(serv_vars['code_dir'])
                            # Run migration check command.
                            output = subprocess.check_output(cmd, shell=True, )
                            if '[ ]' in output:
                                raise Exception("Migrations have not been run for {}".format(service))


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
        if notify:
            notify(msg)
            notify(traceback.format_exc())
        raise ae
    except Exception as e:
        msg = "{}: ERROR : {}".format(prefix, e)
        print(msg)
        if notify:
            notify(msg)
        traceback.print_exc()
        raise e
    else:
        msg = "{}: {}".format(prefix, " | ".join(report))
        print(msg)
        if notify:
            notify(msg)
