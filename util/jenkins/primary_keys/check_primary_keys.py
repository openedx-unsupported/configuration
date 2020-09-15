from __future__ import absolute_import
from __future__ import print_function
import boto3
from botocore.exceptions import ClientError
import sys
import backoff
import pymysql
import click
from datetime import datetime, timedelta, timezone
from six.moves import range

MAX_TRIES = 5
PERIOD = 360
UNIT = 'Percent'

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


class SESBotoWrapper:
    def __init__(self, **kwargs):
        self.client = boto3.client("ses", **kwargs)

    @backoff.on_exception(backoff.expo,
                          ClientError,
                          max_tries=MAX_TRIES)
    def send_email(self, *args, **kwargs):
        return self.client.send_email(*args, **kwargs)


def send_an_email(to_addr, from_addr, primary_keys_message, region):
    ses_client = SESBotoWrapper(region_name=region)

    message = """
    <p>Hello,</p>
    <p>Primary keys of these tables exhausted soon</p>
    <table style='width:100%'>
      <tr style='text-align: left'>
        <th>Database</th>
        <th>Table</th>
        <th>Usage Percentage</th>
        <th>Remaining Days</th>
      </tr>
    """
    for item in range(len(primary_keys_message)):
        message += """
            <tr><td>{Database}</td>
            <td>{Table}</td>
            <td>{UsedPercentage}</td>
            <td>{DaysRemaining}</td>
            </tr>""".format(
            Database=primary_keys_message[item]['database_name'],
            Table=primary_keys_message[item]['table_name'],
            UsedPercentage=primary_keys_message[item]['percentage_of_PKs_consumed'],
            DaysRemaining=primary_keys_message[item]['remaining_days'] if "remaining_days" in primary_keys_message[item] else ''
        )

    message += """</table>"""
    print(("Sending the following as email to {}".format(to_addr)))
    print(message)
    ses_client.send_email(
        Source=from_addr,
        Destination={
            'ToAddresses': [
                to_addr
            ]
        },
        Message={
            'Subject': {
                'Data': 'Primary keys of these table would be exhausted soon',
                'Charset': 'utf-8'
            },
            'Body': {
                'Html':{
                    'Data': message,
                    'Charset': 'utf-8'
                }
            }
        }
    )


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
    ec2_client = EC2BotoWrapper()
    rds_list = []
    try:
        regions_list = ec2_client.describe_regions()
    except ClientError as e:
        print(("Unable to connect to AWS with error :{}".format(e)))
        sys.exit(1)
    for region in regions_list["Regions"]:
        print(("Getting RDS instances in region {}".format(region["RegionName"])))
        rds_client = RDSBotoWrapper(region_name=region["RegionName"])
        response = rds_client.describe_db_instances()
        for instance in response.get('DBInstances'):
            if "test" not in instance["DBInstanceIdentifier"]:
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
        tables_reaching_exhaustion_limit = []
        for rds_instance in rds_list:
            print(("Checking rds instance {}".format(rds_instance["name"])))
            rds_host_endpoint = rds_instance["Endpoint"]
            rds_port = rds_instance["Port"]
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
            for result_table in rds_result:
                table_data = {}
                db_name = result_table[0]
                table_name = result_table[1]
                table_name_combined = "{}.{}".format(db_name, table_name)
                table_percent = result_table[6]
                if table_percent > 70:
                    print(("RDS {} Table {}: Primary keys {}% full".format(
                        rds_instance["name"], table_name_combined, table_percent)))
                    metric_data.append({
                        'MetricName': metric_name,
                        'Dimensions': [{
                            "Name": rds_instance["name"],
                            "Value": table_name_combined
                        }],
                        'Value': table_percent,  # percentage of the usage of primary keys
                        'Unit': UNIT
                    })
                    table_data["database_name"] = rds_instance['name']
                    table_data["table_name"] = table_name_combined
                    table_data["percentage_of_PKs_consumed"] = table_percent
                    remaining_days_table_name = table_name_combined
                    # Hack to transition to metric names with db prepended
                    if table_name == "courseware_studentmodule" and rds_instance["name"] in [
                        "prod-edx-edxapp-us-east-1b-2",
                        "prod-edx-edxapp-us-east-1c-2",
                    ]:
                        remaining_days_table_name = table_name
                        metric_data.append({
                            'MetricName': metric_name,
                            'Dimensions': [{
                                "Name": rds_instance["name"],
                                "Value": table_name
                            }],
                            'Value': table_percent,  # percentage of the usage of primary keys
                            'Unit': UNIT
                        })

                    remaining_days = get_metrics_and_calcuate_diff(namespace, metric_name, rds_instance["name"], table_name, table_percent)
                    if remaining_days:
                        table_data["remaining_days"] = remaining_days
                    tables_reaching_exhaustion_limit.append(table_data)
        if len(metric_data) > 0:
            cloudwatch.put_metric_data(Namespace=namespace, MetricData=metric_data)
        return tables_reaching_exhaustion_limit
    except Exception as e:
        print(("Please see the following exception ", e))
        sys.exit(1)


def get_metrics_and_calcuate_diff(namespace, metric_name, dimension, value, current_consumption):
    cloudwatch = CwBotoWrapper()
    res = cloudwatch.get_metric_stats(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=[
            {
                'Name': dimension,
                'Value': value
            },
        ],
        StartTime=datetime.utcnow() - timedelta(days=180),
        EndTime=datetime.utcnow(),
        Period=86400,
        Statistics=[
            'Maximum',
        ],
        Unit=UNIT
    )
    datapoints = res["Datapoints"]
    days_remaining_before_exhaustion = ''
    if len(datapoints) > 0:
        max_value = max(datapoints, key=lambda x: x['Timestamp'])
        time_diff = datetime.now(timezone.utc) - max_value["Timestamp"]
        last_max_reading = max_value["Maximum"]
        consumed_keys_percentage = 100 - current_consumption
        if current_consumption > last_max_reading:
            current_usage = current_consumption - last_max_reading
            no_of_days = time_diff.days
            increase_over_time_period = current_usage/no_of_days
            days_remaining_before_exhaustion = consumed_keys_percentage/increase_over_time_period
            print(("Days remaining for {table} table on db {db}: {days}".format(table=value,
                                                                 db=dimension,
                                                                 days=days_remaining_before_exhaustion)))
    return days_remaining_before_exhaustion




@click.command()
@click.option('--username', envvar='USERNAME', required=True)
@click.option('--password', envvar='PASSWORD', required=True)
@click.option('--environment', '-e', required=True)
@click.option('--deploy', '-d', required=True,
              help="Deployment (i.e. edx or edge)")
@click.option('--region', multiple=True, help='Default AWS region')
@click.option('--recipient', multiple=True, help='Recipient Email address')
@click.option('--sender', multiple=True, help='Sender email address')
@click.option('--rdsignore', '-i', multiple=True, help='RDS name tags to not check, can be specified multiple times')
def controller(username, password, environment, deploy, region, recipient, sender, rdsignore):
    """
    calls other function and calculate the results
    :param username: username for the RDS.
    :param password: password for the RDS.
    :return: None
    """
    # get list of all the RDSes across all the regions and deployments
    rds_list = get_rds_from_all_regions()
    filtered_rds_list = list([x for x in rds_list if x['name'] not in rdsignore])
    table_list = check_primary_keys(filtered_rds_list, username, password, environment, deploy)
    if len(table_list) > 0:
        send_an_email(recipient[0], sender[0], table_list, region[0])
    sys.exit(0)


if __name__ == "__main__":
    controller()
