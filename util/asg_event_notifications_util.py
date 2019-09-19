from __future__ import absolute_import
from __future__ import print_function
import boto3
import click

@click.group()
def cli():
    pass

def get_asg_infos():

    response = client.describe_auto_scaling_groups(MaxRecords=100)
    auto_scaling_groups = response['AutoScalingGroups']

    return auto_scaling_groups

def get_asg_names():

    asg_names = list()
    for asg in get_asg_infos():
        asg_names.append(asg['AutoScalingGroupName'])

    return asg_names

def get_asg_event_notifications(asg):

    event_notifications = list()
    response = \
        client.describe_notification_configurations(AutoScalingGroupNames=[asg],
            MaxRecords=100)
    notification_configs = response['NotificationConfigurations']
    for notification in notification_configs:
        event_notifications.append(notification['NotificationType'])

    return event_notifications

@click.command()
def show_asg_event_notifications():

    try:

        for asg in get_asg_names():
            event_notifications = get_asg_event_notifications(asg)

            if event_notifications:
                print(("Event notifications: {0} are set for ASG: {1}".format(event_notifications,
                        asg)))
            else:
                print(("No Event Notifications found for ASG {}".format(asg)))
    except Exception as e:

        print(e)

@click.command()
@click.option('--topic_arn', help='The ARN of Amazon SNS topic',
              required=True)
@click.option('--event',
              help='The type of event that causes the notification to be sent'
              , default='autoscaling:EC2_INSTANCE_LAUNCH_ERROR')
@click.option('--confirm', default=False, required=False, is_flag=True,
              help='Set this to create event notification for asg')
def create_asg_event_notifications(
    topic_arn,
    event,
    confirm,
    ):

    asg_names = get_asg_names()
    asg_to_create_event_notifications = list()

    for asg_name in asg_names:

        event_notifications = get_asg_event_notifications(asg_name)

        if event in event_notifications:
             continue
        else:
             asg_to_create_event_notifications.append(asg_name)

    if confirm is False:
        print(("Would have created the event notification for asgs {}".format(asg_to_create_event_notifications)))
    else:
        try:
            for asg in asg_to_create_event_notifications:

                response = \
                    client.put_notification_configuration(AutoScalingGroupName=asg,
                        TopicARN=topic_arn, NotificationTypes=[event])

                print(("Created {0} event notifications for auto scaling group {1}").format(event,
                       asg))
        except Exception as e:
            print(e)

cli.add_command(show_asg_event_notifications)
cli.add_command(create_asg_event_notifications)
if __name__ == '__main__':

    client = boto3.client('autoscaling')
    cli()
