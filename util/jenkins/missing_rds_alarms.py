import boto3
from botocore.exceptions import ClientError
import sys


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
    client_region = boto3.client("ec2")
    rds_list = []
    try:
        regions_list = client_region.describe_regions()
    except ClientError as e:
        print("Unable to connect to AWS with error :{}".format(e))
        sys.exit(1)
    for region in regions_list["Regions"]:
        client = boto3.client("rds", region_name=region["RegionName"])
        response = client.describe_db_instances()
        for instance in response.get('DBInstances'):
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
    client = boto3.client('cloudwatch', region_name=region)
    alarms = client.describe_alarms(AlarmNamePrefix=alarmprefix)
    return len(alarms.get('MetricAlarms'))


def controller():
    """
    Control execution of all other functions
    """
    rds = rds_extractor()
    missing_alarm = []
    # List of RDS we don't care about
    ignore_rds_list = []
    for db in rds:
        if db["name"] not in ignore_rds_list:
            alarms_count = cloudwatch_alarm_checker(db["name"], db["Region"])
            if alarms_count < 1:
                missing_alarm.append(db["name"])
    if len(missing_alarm) > 0:
        print "RDS Name"
        print '\n'.join(str(p) for p in missing_alarm)
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    controller()

