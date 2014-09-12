__author__ = 'e0d'

"""
Retrieves AWS Auto-scaling lifecycle messages from and SQS queue and processes them.  For
the LifeCycleTransition type of autoscaling:EC2_INSTANCE_TERMINATING, ec2 instances are inspected
for an ok_to_retire tag.  If that tag exists, the termination state transition is continued, if not, the
lifecycle timeout is extended.

Because the lifecycle commands are not yet available in boto, these commands are, unfortunately,
run via a subprocess call to the awscli.  This should be fixed when boto is updated.

This script is meant to be run periodically via some process automation, say, Jenkins.

It relies on some component applying the proper tags and performing pre-retirement activities.

./sqs.py -q autoscaling-lifecycle-queue -b /home/you/.virtualenvs/aws/bin --hook MyLifeCycleHook
"""

import argparse
import boto
import json
import subprocess
from boto.sqs.message import RawMessage
import logging
import os
from distutils import spawn

class MissingHostError(Exception):
    pass

class LifecycleHandler:

    INSTANCE_TERMINATION = 'autoscaling:EC2_INSTANCE_TERMINATING'
    TEST_NOTIFICATION = 'autoscaling:TEST_NOTIFICATION'
    NUM_MESSAGES = 10
    WAIT_TIME_SECONDS = 10

    def __init__(self, profile, queue, hook, dry_run, bin_directory=None):
        logging.basicConfig(level=logging.INFO)
        self.queue = queue
        self.hook = hook
        self.profile = profile
        if bin_directory:
            os.environ["PATH"] = bin_directory + os.pathsep + os.environ["PATH"]
        self.aws_bin = spawn.find_executable('aws')
        self.python_bin = spawn.find_executable('python')

        self.base_cli_command ="{python_bin} {aws_bin} --profile {profile} ".format(
            python_bin=self.python_bin,
            aws_bin=self.aws_bin,
            profile=self.profile)

        self.dry_run = dry_run
        self.ec2_con = boto.connect_ec2()
        self.sqs_con = boto.connect_sqs()

    def process_lifecycle_messages(self):
        queue = self.sqs_con.get_queue(self.queue)

        # Needed to get unencoded message for ease of processing
        queue.set_message_class(RawMessage)

        for sqs_message in queue.get_messages(LifecycleHandler.NUM_MESSAGES,
                                              wait_time_seconds=LifecycleHandler.WAIT_TIME_SECONDS):
            body = json.loads(sqs_message.get_body_encoded())
            as_message = json.loads(body['Message'])
            logging.info("Proccessing message {message}.".format(message=as_message))

            if 'LifecycleTransition' in as_message and as_message['LifecycleTransition'] \
                    == LifecycleHandler.INSTANCE_TERMINATION:
                # Convenience vars, set here to avoid messages that don't meet the criteria in
                # the if condition above.
                instance_id = as_message['EC2InstanceId']
                asg = as_message['AutoScalingGroupName']
                token = as_message['LifecycleActionToken']

                try:

                    if self.verify_ok_to_retire(as_message['EC2InstanceId']):

                        logging.info("Host is marked as OK to retire, retiring {instance}".format(
                            instance=instance_id))

                        self.continue_lifecycle(asg, token, self.hook)

                        self.delete_sqs_message(queue, sqs_message, as_message, self.dry_run)

                    else:
                        logging.info("Recording lifecycle heartbeat for instance {instance}".format(
                            instance=instance_id))

                        self.record_lifecycle_action_heartbeat(asg, token, self.hook)
                except MissingHostError as mhe:
                    logging.exception(mhe)
                    # There is nothing we can do to recover from this, so we
                    # still delete the message
                    self.delete_sqs_message(queue, sqs_message, as_message, self.dry_run)

            # These notifications are sent when configuring a new lifecycle hook, they can be
            # deleted safely
            elif as_message['Event'] == LifecycleHandler.TEST_NOTIFICATION:
                self.delete_sqs_message(queue, sqs_message, as_message, self.dry_run)
            else:
                raise NotImplemented("Encountered message, {message_id}, of unexpected type.".format(
                    message_id=as_message['MessageId']))

    def delete_sqs_message(self, queue, sqs_message, as_message, dry_run):
        if not dry_run:
            logging.info("Deleting message with body {message}".format(message=as_message))
            self.sqs_con.delete_message(queue, sqs_message)
        else:
            logging.info("Would have deleted message with body {message}".format(message=as_message))

    def record_lifecycle_action_heartbeat(self, asg, token, hook):

        command = self.base_cli_command + "autoscaling record-lifecycle-action-heartbeat " \
                  "--lifecycle-hook-name {hook} " \
                  "--auto-scaling-group-name {asg} " \
                  "--lifecycle-action-token {token}".format(
            hook=hook,asg=asg,token=token)

        self.run_subprocess_command(command, self.dry_run)

    def continue_lifecycle(self, asg, token, hook):
        command = self.base_cli_command + "autoscaling complete-lifecycle-action --lifecycle-hook-name {hook} " \
                  "--auto-scaling-group-name {asg} --lifecycle-action-token {token} --lifecycle-action-result " \
                  "CONTINUE".format(
                hook=hook, asg=asg, token=token)

        self.run_subprocess_command(command, self.dry_run)

    def run_subprocess_command(self, command, dry_run):

        message = "Running command {command}.".format(command=command)

        if not dry_run:
            logging.info(message)
            try:
                output = subprocess.check_output(command.split(' '))
                logging.info("Output was {output}".format(output=output))
            except Exception as e:
                logging.exception(e)
                raise  e
        else:
            logging.info("Dry run: {message}".format(message=message))

    def get_ec2_instance_by_id(self, instance_id):
        """
        Simple boto call to get the instance based on the instance-id
        """
        instances = self.ec2_con.get_only_instances([instance_id])

        if len(instances) == 1:
            return self.ec2_con.get_only_instances([instance_id])[0]
        else:
            return None

    def verify_ok_to_retire(self, instance_id):
        """
        Ensure that the ok_to_retire tag has been added to the instance in question
        with the value 'true'
        """
        instance = self.get_ec2_instance_by_id(instance_id)

        if instance:
            if 'safe_to_retire' in instance.tags and instance.tags['safe_to_retire'].lower() == 'true':
                logging.info("Instance with id {id} is safe to retire.".format(id=instance_id))
                return True
            else:
                logging.info("Instance with id {id} is not safe to retire.".format(id=instance_id))
                return False
        else:
            # No instance for id in SQS message this can happen if something else
            # has terminated the instances outside of this workflow
            message = "Instance with id {id} is referenced in an SQS message, but does not exist.".\
                format(id=instance_id)
            raise MissingHostError(message)

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--profile',
                        help='The boto profile to use '
                             'per line.',default=None)
    parser.add_argument('-b', '--bin-directory', required=False, default=None,
                        help='The bin directory of the virtual env '
                             'from which to run the AWS cli (optional)')
    parser.add_argument('-q', '--queue', required=True,
                        help="The SQS queue containing the lifecyle messages")

    parser.add_argument('--hook', required=True,
                        help="The lifecyle hook to act upon.")

    parser.add_argument('-d', "--dry-run", dest="dry_run", action="store_true",
                        help='Print the commands, but do not do anything')
    parser.set_defaults(dry_run=False)
    args = parser.parse_args()

    lh = LifecycleHandler(args.profile, args.queue, args.hook, args.dry_run, args.bin_directory)
    lh.process_lifecycle_messages()
