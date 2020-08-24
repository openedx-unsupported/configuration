from __future__ import absolute_import
from __future__ import print_function
import boto3
import click


def get_db_instances(db_engine):

    """ 
    Returns: 
          List of provisioned RDS instances
    """

    if db_engine == "mysql":
        instances = rds.describe_db_instances()['DBInstances']
    elif db_engine == "aurora":
        instances = rds.describe_db_clusters()['DBClusters']
    return instances


def get_db_parameters(db_engine, db_parameter_group, marker):
    
    """ 
    Returns: 
           The detailed parameter list for a particular DB parameter 
           group Using marker as pagination token as at max it returns 
           100 records
    """

    if db_engine == "mysql":
        response = rds.describe_db_parameters(
                       DBParameterGroupName=db_parameter_group, 
                       Marker=marker)
    elif db_engine == "aurora":
        response = rds.describe_db_cluster_parameters(
                       DBClusterParameterGroupName=db_parameter_group, 
                       Marker=marker)
    return response


def check_slow_query_logs(db_engine, db_parameter_group):

    slow_log_enabled = False

    marker = ""
   
    while True:

        if marker is None:
            break

        response = get_db_parameters(db_engine, db_parameter_group, marker)
        marker = response.get('Marker')
        parameters = response.get('Parameters')

        for param in parameters:

            if 'slow_query_log' in param['ParameterName']:

                if 'ParameterValue' in param and param['ParameterValue'] == '1':
                    slow_log_enabled = True
                break

    return slow_log_enabled


@click.command()
@click.option('--db_engine', help='RDS engine: mysql or aurora', required=True)
@click.option('--whitelist', type=(str), multiple=True, help='Whitelisted RDS Instances')
def cli(db_engine, whitelist):

    ignore_rds =  list(whitelist)
    slow_query_logs_disabled_rds = []
    exit_status = 0
    
    dbhosts = get_db_instances(db_engine)

    for dbhost in dbhosts:
       
        if db_engine == "mysql":
            db_identifier = dbhost['DBInstanceIdentifier']
            if db_identifier in ignore_rds or "test" in db_identifier:
                continue

            db_parameter_group = dbhost['DBParameterGroups'][0]['DBParameterGroupName']
        elif db_engine == "aurora":
            db_identifier = dbhost['DBClusterIdentifier']
            if db_identifier in ignore_rds:
                continue

            db_parameter_group = dbhost['DBClusterParameterGroup']

        slow_query_logs_enabled = check_slow_query_logs(db_engine, db_parameter_group)

        if not slow_query_logs_enabled:
            exit_status = 1
            slow_query_logs_disabled_rds.append(db_identifier)

    print(("Slow query logs are disabled for RDS Instances\n{0}".format(slow_query_logs_disabled_rds)))
    exit(exit_status)

if __name__ == '__main__':
         
    rds = boto3.client('rds')
    cli()
