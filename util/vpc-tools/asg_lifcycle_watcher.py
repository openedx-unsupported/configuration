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

    profile = None
    queue = None
    bin = None

    def __init__(self, profile,queue, bin):
        logging.basicConfig(level=logging.INFO)
        self.profile = profile
        self.queue = queue
        self.bin = bin

    def process_lifecycle_messages(self):
        sqs_con = boto.connect_sqs()
        q = sqs_con.get_queue(self.queue)
        q.set_message_class(RawMessage)

        for sqs_message in q.get_messages(10,wait_time_seconds=10):
            body = json.loads(sqs_message.get_body_encoded())
            as_message = json.loads(body['Message'])
            logging.info("Proccessing message {message}.".format(message=as_message))

            if 'LifecycleTransition' in as_message and as_message['LifecycleTransition'] == 'autoscaling:EC2_INSTANCE_TERMINATING':
                # Convenience vars, set here to avoid messages that don't meet the criteria in
                # the if condition above.
                instance_id = as_message['EC2InstanceId']
                asg = as_message['AutoScalingGroupName']
                token = as_message['LifecycleActionToken']

                if self.verify_ok_to_retire(as_message['EC2InstanceId']):

                    logging.info("Host is marked as OK to retire, retiring {instance}".format(
                        instance=instance_id))

                    self.continue_lifecycle(asg,token)
                    sqs_con.delete_message(q,sqs_message)

                else:
                    logging.info("Recording lifecycle heartbeat for instance {instance}".format(
                        instance=instance_id))

                    self.record_lifecycle_action_heartbeat(asg, token)

    def record_lifecycle_action_heartbeat(self, asg, token):

        command = "{path}/python " \
                  "{path}/aws " \
                  "autoscaling record-lifecycle-action-heartbeat " \
                  "--lifecycle-hook-name GetTrackingLogs " \
                  "--auto-scaling-group-name {asg} " \
                  "--lifecycle-action-token {token}".format(
            path=self.bin,asg=asg,token=token)

        self.run_subprocess_command(command)

    def continue_lifecycle(self, asg, token):
        command = "{path}/python " \
                  "{path}/aws autoscaling complete-lifecycle-action --lifecycle-hook-name GetTrackingLogs " \
                  "--auto-scaling-group-name {asg} --lifecycle-action-token {token} --lifecycle-action-result " \
                  "CONTINUE".format(
              path=self.bin, asg=asg, token=token)

        self.run_subprocess_command(command)

    def run_subprocess_command(self,command):
        logging.info("Running command {command}.".format(command=command))

        try:
            output = subprocess.check_output(command.split(' '))
        except Exception, e:
            print e
            print output


    def get_ec2_instance_by_id(self,id):
        """
        Simple boto call to get the instance based on the instance-id
        """
        ec2 = boto.connect_ec2(profile_name=self.profile)

        instances = ec2.get_only_instances([id])

        if len(instances) == 1:
            return ec2.get_only_instances([id])[0]
        else:
            return None


    def verify_ok_to_retire(self,id):
        """
        Ensure that the ok_to_retire tag has been added to the instance in question
        with the value 'true'
        """
        instance = self.get_ec2_instance_by_id(id)

        if instance:

            if 'ok_to_retire' in instance.tags and instance.tags['ok_to_retire'].lower() == 'true':
                return True

            return False
        else:
            # No instance for id in SQS message.
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

    args = parser.parse_args()

    lh = LifecycleHandler(args.profile, args.queue, args.bin)
    lh.process_lifecycle_messages()
