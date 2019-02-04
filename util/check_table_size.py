import boto3
import sys
import pymysql
import logging
import click


logger = logging.getLogger()
logger.setLevel(logging.INFO)
source = boto3.client('rds')


def check_table_growth(password, threshold):
    """
        Return:
             Return list all tables that cross threshold limit
              [
                  {
                    "db": "string",
                    "table": "string",
                    "size": "string",
                  }
              ]
        """
    try:
        table_list = []
        dbs = source.describe_db_instances()
        # List of all RDS in this region
        rds_hosts = dbs.get('DBInstances')
        for rds_host in rds_hosts:
            rds_host_endpoint = rds_host.get('Endpoint').get('Address')
            rds_username = rds_host.get('MasterUsername')
            rds_port = rds_host.get('Endpoint').get('Port')
            logger.info('got event{}'.format(rds_host))
            # Connect to mysql using credentials
            connection = pymysql.connect(host=rds_host_endpoint,
                                         port=rds_port, user=rds_username, password=password)
            # prepare a cursor object using cursor() method
            cursor = connection.cursor()
            # execute SQL query using execute() method.
            cursor.execute("""
            SELECT 
            table_schema as `Database`, 
            table_name AS `Table`, 
            round(((data_length + index_length) / 1024 / 1024), 2) `Size in MB` 
            FROM information_schema.TABLES 
            ORDER BY (data_length + index_length) DESC;
            """)

            rds_result = cursor.fetchall()
            cursor.close()
            connection.close()
            for tables in rds_result:
                temp_dict = {}
                if tables[2] > threshold:
                    temp_dict["db"] = tables[0]
                    temp_dict["table"] = tables[1]
                    temp_dict["size"] = tables[2]
                    table_list.append(temp_dict)
                    logger.info('got event{}'.format(tables))
        return table_list
    except Exception as ex:
        print ex
        sys.exit(1)


def send_email(table_list):
    html = ''
    for table_data in table_list:
        for key, value in table_data.items():
            html += '<p>%s</p>' % key
            html += '<li>' + str(value) + '</li>'

        client = boto3.client('ses')
        client.send_email(
            Source='sandbox-notifications@edx.org',
            Destination={
                'ToAddresses': ["ihassan@edx.org"]
            },
            Message={
                'Subject': {
                    'Data': 'These tables exceed the threshold',
                    'Charset': 'utf-8'
                },
                'Body': {
                    'Html': {
                        'Data': html,
                        'Charset': 'utf-8'
                    }
                }
            },
        )


@click.command()
@click.option('--password', required=True, help='Password for RDS')
@click.option('--threshold', required=True, help='Threshold for tables')
def lambda_handler(password, threshold):
    """
    Control execution of all other functions
    Arguments:
        Password (str):
            Get this from cli args
        Threshold (str):
            Get this from cli args
    """
    table_list = check_table_growth(password, threshold)
    if len(table_list) > 0:
        send_email(table_list)


if __name__ == '__main__':
    lambda_handler()

