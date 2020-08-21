from __future__ import absolute_import
from __future__ import print_function
import boto3
from botocore.exceptions import ClientError
import sys
import backoff
import pymysql
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


def rds_extractor(environment):
    """
    Return list of all RDS instances across all the regions
    Returns:
        [
            {
                'name': name,
                'Endpoint': Endpoint of RDS
                'Port': Port of RDS
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
            if environment in instance.get("Endpoint").get("Address") and "test" not in instance["DBInstanceIdentifier"]:
                temp_dict = {}
                temp_dict["name"] = instance["DBInstanceIdentifier"]
                temp_dict["Endpoint"] = instance.get("Endpoint").get("Address")
                temp_dict["Port"] = instance.get("Port")
                rds_list.append(temp_dict)
    return rds_list


def check_queries_running(rds_list, username, password):
    """
        Return:
             Return list of currently running queries
              [
                  {
                    "id": "string",
                    "user": "string",
                    "host": "string",
                    "command": "string",
                    "time": "integer",
                    "state": "string",
                    "info": "string"
                  }
              ]
        """
    try:
        process_list = []
        for item in rds_list:
            rds_host_endpoint = item["Endpoint"]
            rds_port = item["Port"]
            connection = pymysql.connect(host=rds_host_endpoint,
                                         port=rds_port, user=username, password=password)
            # prepare a cursor object using cursor() method
            cursor = connection.cursor()
            # execute SQL query using execute() method.
            cursor.execute("""
                            SELECT * FROM INFORMATION_SCHEMA.PROCESSLIST
                            """)

            rds_result = cursor.fetchall()
            cursor.close()
            connection.close()
            for process in rds_result:
                temp_dict = {}
                temp_dict["id"] = process[0]
                temp_dict["user"] = process[1]
                temp_dict["host"] = process[2]
                temp_dict["command"] = process[4]
                temp_dict["time"] = process[5]
                temp_dict["state"] = process[6]
                temp_dict["info"] = process[7]
                process_list.append(temp_dict)
        return process_list
    except Exception as ex:
        print(ex)
        sys.exit(1)


@click.command()
@click.option('--username', envvar='USERNAME', required=True)
@click.option('--password', envvar='PASSWORD', required=True)
@click.option('--environment', required=True, help='Use to identify the environment')
@click.option('--rdsignore', '-i', multiple=True, help='RDS name tags to not check, can be specified multiple times')
def controller(username, password, environment, rdsignore):
    """
    Control execution of all other functions
    Arguments:
        username (str):
            Get this from cli args

        password (str):
            Get this from cli args

        environment (str):
            Get this from cli args
    """
    rds_list = rds_extractor(environment)
    filtered_rds_list = list([x for x in rds_list if x['name'] not in rdsignore])
    process_list = check_queries_running(filtered_rds_list, username, password)
    if len(process_list) > 0:
        format_string = "{:<20}{:<20}{:<30}{:<20}{:<20}{:<70}{}"
        print((format_string.format("Query ID", "User Name", "Host", "Command", "Time Executed", "State", "Info")))
        for items in process_list:
            print((format_string.format(items["id"], items["user"], items["host"], items["command"],
                                       str(items["time"]) + " sec", items["state"], items["info"])))
    exit(0)


if __name__ == '__main__':
    controller()

