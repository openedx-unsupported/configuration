from __future__ import absolute_import
from __future__ import print_function
import boto3
from botocore.exceptions import ClientError
import sys
import backoff
import pymysql
import time
import uuid
import click
import re
import splunklib.client as splunk_client

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
        rds_client = RDSBotoWrapper(region_name=region["RegionName"])
        response = rds_client.describe_db_instances()
        for instance in response.get('DBInstances'):
            if environment in instance.get("Endpoint").get("Address") and "test" not in instance["DBInstanceIdentifier"]:
                temp_dict = {}
                temp_dict["name"] = instance["DBInstanceIdentifier"]
                temp_dict["ARN"] = instance["DBInstanceArn"]
                temp_dict["Region"] = region["RegionName"]
                temp_dict["Endpoint"] = instance.get("Endpoint").get("Address")
                temp_dict["Username"] = instance.get("MasterUsername")
                temp_dict["Port"] = instance.get("Port")
                rds_list.append(temp_dict)
    return rds_list


def rds_controller(rds_list, username, password, hostname, splunkusername, splunkpassword, port, indexname):
    for item in rds_list:
        rds_host_endpoint = item["Endpoint"]
        rds_port = item["Port"]
        connection = pymysql.connect(host=rds_host_endpoint, port=rds_port,
                                     user=username, password=password)
        cursor = connection.cursor()
        cursor.execute("""
                      SHOW ENGINE INNODB STATUS;
                    """)
        rds_result = cursor.fetchall()
        cursor.close()
        connection.close()
        regex = r"-{4,}\sLATEST DETECTED DEADLOCK\s-{4,}\s((.*)\s)*?-{4,}"
        global_str = ""
        for row in rds_result:
            matches = re.finditer(regex, row[2])
            for matchNum, match in enumerate(matches, start=1):
                global_str = match.group()
        expr = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
        global_str = re.sub(expr, '', global_str)
        #to avoid empty dead locks
        if len(global_str) > 0:
            service = splunk_client.connect(host=hostname, port=port, username=splunkusername, password=splunkpassword)
            myindex = service.indexes[indexname]
            # Open a socket
            mysocket = myindex.attach(host=rds_host_endpoint, source="INNODB STATUS", sourcetype="RDS")

            # Send events to it
            mysocket.send(str.encode(global_str))

            # Close the socket
            mysocket.close()


@click.command()
@click.option('--username', envvar='USERNAME', required=True)
@click.option('--password', envvar='PASSWORD', required=True)
@click.option('--environment', required=True, help='Use to identify the environment')
@click.option('--hostname', required=True, help='Use to identify the splunk hostname')
@click.option('--splunkusername', envvar='SPLUNKUSERNAME', required=True)
@click.option('--splunkpassword', envvar='SPLUNKPASSWORD', required=True)
@click.option('--port', required=True, help='Use to identify the splunk port')
@click.option('--indexname', required=True, help='Use to identify the splunk index name')
@click.option('--rdsignore', '-i', multiple=True, help='RDS name tags to not check, can be specified multiple times')
def main(username, password, environment, hostname, splunkusername, splunkpassword, port, indexname, rdsignore):
    rds_list = rds_extractor(environment)
    filtered_rds_list = list([x for x in rds_list if x['name'] not in rdsignore])
    rds_controller(filtered_rds_list, username, password, hostname, splunkusername, splunkpassword, port, indexname)


if __name__ == '__main__':
    main()

