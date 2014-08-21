__author__ = 'edward'

"""
Retrieves AWS Auto-scaling lifecycle messages from and SQS queue and processes them.  For
the LifeCycleTransition type of autoscaling:EC2_INSTANCE_TERMINATING, ec2 instances are inspected
for an ok_to_retire tag.  If that tag exists, the termination state transition is continued, if not, the
lifecycle timeout is extended.

Because the lifecycle commands are not yet available in boto, these commands are, unfortunately,
run via a subprocess call to the awscli.  This should be fixed when boto is updated.

This script is meant to be run periodically via some process automation, say, Jenkins.

It relies on some component applying the proper tags and performing pre-retirement activities.

./sqs.py -q loadtest-edx_autoscaling-lifecycle -b ~/.virtualenvs/aws/bin
"""

import argparse
import boto
import json
import subprocess
from boto.sqs.message import RawMessage
import logging

class LifecycleHandler:

    INSTANCE_TERMINATION = 'autoscaling:EC2_INSTANCE_TERMINATING'
    TEST_NOTIFICATION = 'autoscaling:TEST_NOTIFICATION'
    NUM_MESSAGES = 10
    WAIT_TIME_SECONDS = 10

    def __init__(self, profile,queue, hook, bin, dry_run):
        logging.basicConfig(level=logging.INFO)
        self.profile = profile
        self.queue = queue
        self.hook = hook
        self.bin = bin
        self.dry_run = dry_run
        self.ec2 = boto.connect_ec2(profile_name=self.profile)

    def process_lifecycle_messages(self):
        sqs_con = boto.connect_sqs()
        queue = sqs_con.get_queue(self.queue)

        # Needed to get unencoded message for ease of processing
        queue.set_message_class(RawMessage)

        for sqs_message in queue.get_messages(self.NUM_MESSAGES,
                                              wait_time_seconds=self.WAIT_TIME_SECONDS):
            body = json.loads(sqs_message.get_body_encoded())
            as_message = json.loads(body['Message'])
            logging.info("Proccessing message {message}.".format(message=as_message))

            if 'LifecycleTransition' in as_message and as_message['LifecycleTransition'] == self.INSTANCE_TERMINATION:
                # Convenience vars, set here to avoid messages that don't meet the criteria in
                # the if condition above.
                instance_id = as_message['EC2InstanceId']
                asg = as_message['AutoScalingGroupName']
                token = as_message['LifecycleActionToken']

                if self.verify_ok_to_retire(as_message['EC2InstanceId']):

                    logging.info("Host is marked as OK to retire, retiring {instance}".format(
                        instance=instance_id))

                    self.continue_lifecycle(asg,token,self.hook)

                    if not self.dry_run:
                        logging.info("Deleting message with body {message}".format(message=as_message))
                        sqs_con.delete_message(queue,sqs_message)
                    else:
                        logging.info("Would have deleted message with body {message}".format(message=as_message))

                else:
                    logging.info("Recording lifecycle heartbeat for instance {instance}".format(
                        instance=instance_id))

                    self.record_lifecycle_action_heartbeat(asg, token,self.hook)
            elif as_message['Event'] == self.TEST_NOTIFICATION:
                    if not self.dry_run:
                        logging.info("Deleting message with body {message}".format(message=as_message))
                        sqs_con.delete_message(queue,sqs_message)
                    else:
                        logging.info("Would have deleted message with body {message}".format(message=as_message))


    def record_lifecycle_action_heartbeat(self, asg, token, hook):

        command = "{path}/python " \
                  "{path}/aws " \
                  "autoscaling record-lifecycle-action-heartbeat " \
                  "--lifecycle-hook-name {hook} " \
                  "--auto-scaling-group-name {asg} " \
                  "--lifecycle-action-token {token}".format(
            path=self.bin,hook=hook,asg=asg,token=token)

        self.run_subprocess_command(command, self.dry_run)

    def continue_lifecycle(self, asg, token, hook):
        command = "{path}/python " \
                  "{path}/aws autoscaling complete-lifecycle-action --lifecycle-hook-name {hook} " \
                  "--auto-scaling-group-name {asg} --lifecycle-action-token {token} --lifecycle-action-result " \
                  "CONTINUE".format(
              path=self.bin, hook=hook, asg=asg, token=token)

        self.run_subprocess_command(command, self.dry_run)

    def run_subprocess_command(self,command, dry_run):

        logging.info("Running command {command}.".format(command=command))

        if not dry_run:
            try:
                output = subprocess.check_output(command.split(' '))
                logging.info("Output was {output}".format(output=output))
            except Exception as e:
                logging.exception(e)
                raise  e


    def get_ec2_instance_by_id(self,id):
        """
        Simple boto call to get the instance based on the instance-id
        """
        instances = self.ec2.get_only_instances([id])

        if len(instances) == 1:
            return self.ec2.get_only_instances([id])[0]
        else:
            return None


    def verify_ok_to_retire(self,id):
        """
        Ensure that the ok_to_retire tag has been added to the instance in question
        with the value 'true'
        """
        instance = self.get_ec2_instance_by_id(id)

        if instance:
            if 'safe_to_retire' in instance.tags and instance.tags['safe_to_retire'].lower() == 'true':
                logging.info("Instance with id {id} is safe to retire.".format(id=id))
                return True
            else:
                logging.info("Instance with id {id} is not safe to retire.".format(id=id))
                return False
        else:
            # No instance for id in SQS message this can happen if something else
            # has terminated the instances outside of this workflow
            logging.warn("Instance with id {id} is referenced in an SQS message, but does not exist.")
            return True

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--profile',
                        help='The boto profile to use '
                             'per line.',default=None)
    parser.add_argument('-b', '--bin', required=True,
                        help='The bin directory of the virtual env '
                             'from which tor run the AWS cli')
    parser.add_argument('-q', '--queue', required=True,
                        help="The SQS queue containing the lifecyle messages")

    parser.add_argument('--hook', required=True,
                        help="The lifecyle hook to act upon.")


    parser.add_argument('-d', "--dry-run", dest="dry_run", action="store_true",
                        help='Print the commands, but do not do anything')
    parser.set_defaults(dry_run=False)
    args = parser.parse_args()

    lh = LifecycleHandler(args.profile, args.queue, args.hook, args.bin, args.dry_run)
    lh.process_lifecycle_messages()
