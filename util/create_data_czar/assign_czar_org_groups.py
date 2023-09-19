"""
assign_czar_org_groups.py

Assigns data czars to the iam groups for their org based on the configuration specificed in the analytics-exporter
repository, https://github.com/openedx/edx-analytics-exporter/blob/master/sample-config.yaml

Assumes that a group for the org has already been created using the create_org_data_czar_polcy.py script.

Assumes that the data czars email is their IAM user name.

Assumes that org names are consistent in s3 and the yaml config file and IAM.

"""

import argparse
import boto
import yaml
import sys



parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', help='Path to the Analytics YAML file containing '
                                         'the organization meta-data which is located ')
parser.add_argument('-p', '--profile', help='The IAM profile to use when '
                                            'adding user to groups')
args = parser.parse_args()


org_group_name_template = "edx-course-data-{org}"

with open(args.file) as config:
    data = yaml.load(config)


iam_connection = boto.connect_iam(profile_name=args.profile)

for group, group_info in data['organizations'].items():
    print(f"Adding {group_info['recipients']} to group {group}.")

    # Add to the group providing general permissions for all data czars.
    try:
        for user in group_info['recipients']:
            iam_connection.add_user_to_group('analytics-edx-course-data-s3-ro', user)
    except Exception as e:
        print(e)

    # Add to the org specific group
    try:
        pass
        for user in group_info['recipients']:
            iam_connection.add_user_to_group(org_group_name_template.format(org=group), user)
    except Exception as e:
        print(e)

sys.exit(0)
