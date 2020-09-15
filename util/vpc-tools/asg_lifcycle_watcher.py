from __future__ import absolute_import
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
import boto3
import json
import subprocess
import logging
import os
from distutils import spawn

class MissingHostError(Exception):
    pass

class LifecycleHandler:

    INSTANCE_TERMINATION = 'autoscaling:EC2_INSTANCE_TERMINATING'
    TEST_NOTIFICATION = 'autoscaling:TEST_NOTIFICATION'
    NUM_MESSAGES = 10
    WAIT_TIME_SECONDS = 1
    VISIBILITY_TIMEOUT = 10

    def __init__(self, region, queue, hook, dry_run, bin_directory=None):
        logging.basicConfig(level=logging.INFO)
        self.queue = queue
        self.hook = hook
        self.region = region
        if bin_directory:
            os.environ["PATH"] = bin_directory + os.pathsep + os.environ["PATH"]
        self.aws_bin = spawn.find_executable('aws')
        self.python_bin = spawn.find_executable('python')

        self.base_cli_command ="{python_bin} {aws_bin} ".format(
            python_bin=self.python_bin,
            aws_bin=self.aws_bin)
        
        if self.region:
            self.base_cli_command += "--region {region} ".format(region=self.region)

        self.dry_run = args.dry_run
        self.ec2_con = boto3.client('ec2',region_name=self.region)
        self.sqs_con = boto3.client('sqs',region_name=self.region)

    def process_lifecycle_messages(self):
        queue_url = self.sqs_con.get_queue_url(QueueName=self.queue)['QueueUrl']
        queue = boto3.resource('sqs', region_name=self.region).Queue(queue_url)

        for sqs_message in self.sqs_con.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=LifecycleHandler.NUM_MESSAGES, VisibilityTimeout=LifecycleHandler.VISIBILITY_TIMEOUT,
                                              WaitTimeSeconds=LifecycleHandler.WAIT_TIME_SECONDS).get('Messages', []):
            body = json.loads(sqs_message['Body'])
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
            self.sqs_con.delete_message(QueueUrl=queue.url, ReceiptHandle=sqs_message['ReceiptHandle'])
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
        reservations = self.ec2_con.describe_instances(InstanceIds=[instance_id]).get('Reservations', [])
        instances = []
        if len(reservations) == 1:
            instances = reservations[0].get('Instances', [])
        if len(instances) == 1:
            return self.ec2_con.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]
        else:
            return None

    def verify_ok_to_retire(self, instance_id):
        """
        Ensure that the safe_to_retire tag has been added to the instance in question
        with the value 'true'
        """
        instance = self.get_ec2_instance_by_id(instance_id)
        tags_dict = {}

        if instance:
            tags_dict = {}
            for t in instance['Tags']:
                tags_dict[t['Key']] = t['Value']
            if 'safe_to_retire' in tags_dict and tags_dict['safe_to_retire'].lower() == 'true':
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
    parser.add_argument('-r', '--region',
                        help='The aws region to use '
                             'per line.',default='us-east-1')
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

    lh = LifecycleHandler(args.region, args.queue, args.hook, args.dry_run, args.bin_directory)
    lh.process_lifecycle_messages()
