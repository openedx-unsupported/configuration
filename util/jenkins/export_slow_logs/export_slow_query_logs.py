import boto3
from botocore.exceptions import ClientError
import sys
import backoff
import pymysql
import time
import uuid


MAX_TRIES = 5


class CWBotoWrapper:
    def __init__(self, **kwargs):
        self.client = boto3.client("logs", **kwargs)

    @backoff.on_exception(backoff.expo, ClientError, max_tries=MAX_TRIES)
    def put_log_events(self, **kwargs):
        return self.client.put_log_events(**kwargs)

    @backoff.on_exception(backoff.expo, ClientError, max_tries=MAX_TRIES)
    def create_log_stream(self, **kwargs):
        return self.client.create_log_stream(**kwargs)

    @backoff.on_exception(backoff.expo, ClientError, max_tries=MAX_TRIES)
    def create_log_group(self, **kwargs):
        return self.client.create_log_group(**kwargs)


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
        print("Unable to connect to AWS with error :{}".format(e))
        sys.exit(1)
    for region in regions_list["Regions"]:
        client = RDSBotoWrapper(region_name=region["RegionName"])
        response = client.describe_db_instances()
        for instance in response.get('DBInstances'):
            temp_dict = {}
            temp_dict["name"] = instance["DBInstanceIdentifier"]
            temp_dict["ARN"] = instance["DBInstanceArn"]
            temp_dict["Region"] = region["RegionName"]
            temp_dict["Endpoint"] = instance.get("Endpoint").get("Address")
            temp_dict["Username"] = instance.get("MasterUsername")
            temp_dict["Port"] = instance.get("Port")
            rds_list.append(temp_dict)
    return rds_list


def rds_controller(rds_list, username, password):
    for item in rds_list:
        rds_host_endpoint = item["Endpoint"]
        rds_username = item["Username"]
        rds_port = item["Port"]
        connection = pymysql.connect(host=rds_host_endpoint, port=rds_port,
                                     user=username, password=password)
        cursor = connection.cursor()
        cursor.execute("""
                      SELECT *
                      FROM mysql.slow_log
                      WHERE start_time > DATE_ADD(NOW(), INTERVAL -1 HOUR);
                    """)
        rds_result = cursor.fetchall()
        cursor.close()
        connection.close()
        cw_logs = []
        sequencetoken = None
        client = CWBotoWrapper()
        try:
            client.create_log_group(logGroupName=rds_host_endpoint)
            print('Created CloudWatch log group named "%s"', rds_host_endpoint)
        except ClientError:
            print('CloudWatch log group named "%s" already exists', rds_host_endpoint)
        LOG_STREAM = time.strftime('%Y-%m-%d') + "/[$LATEST]" + uuid.uuid4().hex
        client.create_log_stream(logGroupName=rds_host_endpoint, logStreamName=LOG_STREAM)
        for tables in rds_result:
            temp = {}
            temp["timestamp"] = int(tables[0].strftime("%s")) * 1000
            temp["message"] = "User@Host: " + str(tables[1]) + \
                "Query_time: " + str(tables[2]) + " Lock_time: " + str(tables[3]) + \
                " Rows_sent: " + str(tables[4]) + " Rows_examined: " + str(tables[5]) +\
                "Slow Query: " + str(tables[10])
            cw_logs.append(temp)
        if sequencetoken == None:
            response = client.put_log_events(
                                    logGroupName=rds_host_endpoint,
                                    logStreamName=LOG_STREAM,
                                    logEvents=cw_logs
                                    )
        else:
            response = client.put_log_events(
                logGroupName=rds_host_endpoint,
                logStreamName="test",
                logEvents=cw_logs,
                sequenceToken=sequencetoken
            )
        sequencetoken = response["nextSequenceToken"]


@click.command()
@click.option('--username', envvar='USERNAME', required=True)
@click.option('--password', envvar='PASSWORD', required=True)
def main(username, password):
    rds_list = rds_extractor()
    rds_controller(rds_list, username, password)


if __name__ == '__main__':
    main()

