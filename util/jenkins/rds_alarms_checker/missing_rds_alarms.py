from __future__ import absolute_import
from __future__ import print_function
import boto3
from botocore.exceptions import ClientError
import sys
import backoff
import click

MAX_TRIES = 5


class EC2BotoWrapper:
    def __init__(self):
        self.client = boto3.client("ec2")

    @backoff.on_exception(backoff.expo, ClientError, max_tries=MAX_TRIES)
    def describe_regions(self):
        return self.client.describe_regions()


class RDSBotoWrapper:
    def __init__(self, **kwargs):
        self.client = boto3.client("rds", **kwargs)

    @backoff.on_exception(backoff.expo, ClientError, max_tries=MAX_TRIES)
    def describe_db_instances(self):
        return self.client.describe_db_instances()


class CWBotoWrapper:
    def __init__(self, **kwargs):
        self.client = boto3.client("cloudwatch", **kwargs)

    @backoff.on_exception(backoff.expo, ClientError, max_tries=MAX_TRIES)
    def describe_alarms(self, **kwargs):
        return self.client.describe_alarms(**kwargs)


def rds_extractor():
    """
    Return list of all RDS instances across all the regions
    Returns:
        [
            {
                'name': name,
                'ARN': RDS ARN,
                'Region': Region of RDS
            }
        ]
    """
    client_region = EC2BotoWrapper()
    rds_list = []
    try:
        regions_list = client_region.describe_regions()
    except ClientError as e:
        print(("Unable to connect to AWS with error :{}".format(e)))
        sys.exit(1)
    for region in regions_list["Regions"]:
        client = RDSBotoWrapper(region_name=region["RegionName"])
        response = client.describe_db_instances()
        for instance in response.get('DBInstances'):
            if "test" not in instance["DBInstanceIdentifier"]:
                temp_dict = {}
                temp_dict["name"] = instance["DBInstanceIdentifier"]
                temp_dict["ARN"] = instance["DBInstanceArn"]
                temp_dict["Region"] = region["RegionName"]
                rds_list.append(temp_dict)
    return rds_list


def cloudwatch_alarm_checker(alarmprefix, region):
    """
    Return number of alarms associated with given RDS instance
    Returns:
        len(alarms): integer
    """
    client = CWBotoWrapper(region_name=region)
    alarms = client.describe_alarms(AlarmNamePrefix=alarmprefix)
    return len(alarms.get('MetricAlarms'))


@click.command()
@click.option('--whitelist', type=(str), multiple=True, help='List of Whitelisted RDS')
def controller(whitelist):
    """
    Control execution of all other functions
    """
    rds = rds_extractor()
    missing_alarm = []
    # List of RDS we don't care about
    ignore_rds_list = list(whitelist)
    for db in rds:
        if db["name"] not in ignore_rds_list:
            alarms_count = cloudwatch_alarm_checker(db["name"], db["Region"])
            if alarms_count < 1:
                missing_alarm.append(db["name"])
    if len(missing_alarm) > 0:
        print("RDS Name")
        print('\n'.join(str(p) for p in missing_alarm))
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    controller()
