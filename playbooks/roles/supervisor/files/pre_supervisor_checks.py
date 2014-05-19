# Get the tags for this instance
import argparse
import boto
import boto.utils
import os
import subprocess
import hipchat
import traceback


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Enable all services that are in the services tag of this ec2 instance.")
    parser.add_argument("-a","--available",
        help="The location of the available services.")
    parser.add_argument("-e","--enabled",
        help="The location of the enabled services.")

    hipchat_args = parser.add_argument_group("hipchat",
            "Args for hipchat notification.")
    hipchat_args.add_argument("-c","--hipchat-api-key",
        help="Hipchat token if you want to receive notifications via hipchat.")
    hipchat_args.add_argument("-r","--hipchat-room",
        help="Room to send messages to.")

    args = parser.parse_args()

    hc = None
    report = []
    hc_user = "PreSupervisor"

    if args.hipchat_api_key:
        hc = hipchat.HipChat(token=args.hipchat_api_key)

    try:
        ec2 = boto.connect_ec2()
        instance_id = boto.utils.get_instance_metadata()['instance-id']
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
                        # Link to available service.
                        available_file = os.path.join(args.available, "{}.conf".format(service))
                        link_location = os.path.join(args.enabled, "{}.conf".format(service))
                        if os.path.exists(available_file):
                            subprocess.call("ln -sf {} {}".format(available_file, link_location), shell=True)
                            report.append("Linking service: {}".format(service))
                        else:
                            raise Exception("No conf available for service: {}".format(link_location))
    except Exception as e:
        msg = "{}: pre_supervisor failed with exception: {}".format(instance_id, traceback.format_exc())
        print(msg)
        if hc:
            hc.message_room(room_id=args.hipchat_room,
            message_from=hc_user,
            message=msg)
    finally:
        print("\n".join(report))
        if hc:
            hc.message_room(room_id=args.hipchat_room,
                message_from=hc_user,
                message="{}:\n{}".format(instance_id,"\n".join(report)))

