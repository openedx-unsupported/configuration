import boto3
from botocore.exceptions import ClientError
import sys
import backoff
import pymysql
import click
from datetime import datetime, timedelta

MAX_TRIES = 5
PERIOD = 360
UNIT = 'percent'

class EC2BotoWrapper:
    def __init__(self):
        self.client = boto3.client("ec2")

    @backoff.on_exception(backoff.expo,
                          ClientError,
                          max_tries=MAX_TRIES)
    def describe_regions(self):
        return self.client.describe_regions()


class CwBotoWrapper():
    def __init__(self):
        self.client = boto3.client('cloudwatch')

    @backoff.on_exception(backoff.expo,
                          ClientError,
                          max_tries=MAX_TRIES)
    def list_metrics(self, *args, **kwargs):
        return self.client.list_metrics(*args, **kwargs)

    @backoff.on_exception(backoff.expo,
                          ClientError,
                          max_tries=MAX_TRIES)
    def put_metric_data(self, *args, **kwargs):
        return self.client.put_metric_data(*args, **kwargs)

    @backoff.on_exception(backoff.expo,
                          ClientError,
                          max_tries=MAX_TRIES)
    def get_metric_stats(self, *args, **kwargs):
        return self.client.get_metric_statistics(*args, **kwargs)


class RDSBotoWrapper:
    def __init__(self, **kwargs):
        self.client = boto3.client("rds", **kwargs)

    @backoff.on_exception(backoff.expo,
                          ClientError,
                          max_tries=MAX_TRIES)
    def describe_db_instances(self):
        return self.client.describe_db_instances()


def get_rds_from_all_regions():
    """
    Gets a list of RDS instances across all the regions and deployments in AWS

    :returns:
    list of all RDS instances across all the regions
        [
            {
                'name': name of RDS,
                'Endpoint': Endpoint of RDS
                'Port': Port of RDS
            }
        ]
    name (string)
    Endpoint (string)
    Port (string)
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
            temp_dict = dict()
            temp_dict["name"] = instance["DBInstanceIdentifier"]
            temp_dict["Endpoint"] = instance.get("Endpoint").get("Address")
            temp_dict["Port"] = instance.get("Port")
            rds_list.append(temp_dict)
    return rds_list


def check_primary_keys(rds_list, username, password, environment, deploy):
    """
    :param rds_list:
    :param username:
    :param password:

    :returns:
         Return list of all tables that cross threshold limit
              [
                  {
                    "name": "string",
                    "db": "string",
                    "table": "string",
                    "size": "string",
                  }
              ]
    """
    cloudwatch = CwBotoWrapper()
    metric_name = 'used_key_space'
    namespace = "rds-primary-keys/{}-{}".format(environment, deploy)
    try:
        table_list = []
        metric_data = []
        for item in rds_list:
            rds_host_endpoint = item["Endpoint"]
            rds_port = item["Port"]
            connection = pymysql.connect(host=rds_host_endpoint,
                                         port=rds_port,
                                         user=username,
                                         password=password)
            # prepare a cursor object using cursor() method
            cursor = connection.cursor()
            # execute SQL query using execute() method.
            # this query will return the tables with usage in percentage, result is limited to 10
            cursor.execute("""
            SELECT
                table_schema,
                table_name,
                column_name,
                column_type,
                auto_increment,
                max_int,
                ROUND(auto_increment/max_int*100,2) AS used_pct
            FROM
                (
                 SELECT
                    table_schema,
                    table_name,
                    column_name,
                    column_type,
                    auto_increment,
                    pow
                        (2,
                            case data_type
                            when 'tinyint' then 7
                            when 'smallint' then 15
                            when 'mediumint' then 23
                            when 'int' then 31
                            when 'bigint' then 63
                            end
                        +(column_type like '% unsigned'))-1
                    as max_int
                 FROM
                    information_schema.tables t
                    JOIN information_schema.columns c
                        USING (table_schema,table_name)
                        WHERE t.table_schema not in ('mysql','information_schema','performance_schema')
                        AND t.table_type = 'base table'
                        AND c.extra LIKE '%auto_increment%'
                        AND t.auto_increment IS NOT NULL
                 )
            TMP ORDER BY used_pct desc
            LIMIT 10;
            """)
            rds_result = cursor.fetchall()
            cursor.close()
            connection.close()

            for table in rds_result:
                if table[6] > 70:
                    metric_data.append({
                        'MetricName': metric_name,
                        'Dimensions': [{
                            "Name": item["name"],
                            "Value": table[1]
                        }],
                        'Value': table[6],  # percentage of the usage of primary keys
                        'Unit': 'percent'
                    })

            if len(metric_data) > 0:
                cloudwatch.put_metric_data(Namespace=namespace, MetricData=metric_data)
        return table_list
    except Exception as e:
        print("Please see the following exception ", e)
        sys.exit(1)


def get_metrics_and_calcuate_diff(namespace, metric_name, dimension, value, current_consumption):
    cloudwatch = CwBotoWrapper()
    time = datetime.now() - timedelta(days=1)
    delta = time.strftime("%Y, %m, %d")
    res = cloudwatch.get_metric_stats(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=[
            {
                'Name': dimension,
                'Value': value
            },
        ],
        StartTime=datetime(int(delta)),
        EndTime=datetime.now().strftime("%Y, %m, %d"),
        Period=360,
        Statistics=[
            'Maximum',
        ],
        Unit='Count'
    )
    last_max_reading = res["Datapoints"][0]["Maximum"]
    cosnumed_keys_percentage = 100 - current_consumption
    days_remaining_before_exhaustion = cosnumed_keys_percentage/(current_consumption -
                                                                 last_max_reading)


@click.command()
@click.option('--username', envvar='USERNAME', required=True)
@click.option('--password', envvar='PASSWORD', required=True)
@click.option('--environment', '-e', required=True)
@click.option('--deploy', '-d', required=True,
              help="Deployment (i.e. edx or edge)")
def controller(username, password, environment, deployment):
    """
    calls other function and calculate the results
    :param username: username for the RDS.
    :param password: password for the RDS.
    :return: None
    """

    # get list of all the RDSes across all the regions and deployments
    rds_list = get_rds_from_all_regions()
    table_list = check_primary_keys(rds_list, username, password, environment, deployment)
    cloudwatch = CwBotoWrapper()
    response = cloudwatch.list_metrics(Namespace=NAMESPACE,
                                       MetricName=METRIC_NAME)

    exit(0)
