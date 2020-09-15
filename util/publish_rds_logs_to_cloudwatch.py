#!/usr/bin/python3
"""
Publish RDS logs to cloudwatch 
Example:
   ./publish_rds_logs_to_cloudwatch --db_engine mysql --db_identifier edx-mysql-db
   ./publish_rds_logs_to_cloudwatch --db_engine aurora --db_identifier edx-aurora-cluster

"""
from __future__ import absolute_import
from __future__ import print_function
import boto3
import argparse

def get_client():

    rds_client = boto3.client('rds')
    return rds_client

def publish_rds_logs_to_cloudwatch(db_engine,db_identifier,logs_to_publish):

    client = get_client()
    try:
        if db_engine == "mysql":
            response = client.modify_db_instance(
                DBInstanceIdentifier=db_identifier,
                CloudwatchLogsExportConfiguration={
                    'EnableLogTypes': [
                         logs_to_publish
                     ]
                }
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                id=response["DBInstance"]["DBInstanceIdentifier"]
                logs_exports_to_cloudwatch=response["DBInstance"]["EnabledCloudwatchLogsExports"]
                print(("RDS MySQL DB {} logs {} are enabled to exports to cloudwatch" \
                      .format(id,logs_exports_to_cloudwatch)))
        elif db_engine == "aurora":
            response = client.modify_db_cluster(
                DBClusterIdentifier=db_identifier,
                CloudwatchLogsExportConfiguration={ 
                    'EnableLogTypes':[
                        logs_to_publish
                     ]
                }
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                id=response["DBCluster"]["DBClusterIdentifier"]
                logs_exports_to_cloudwatch=response["DBCluster"]["EnabledCloudwatchLogsExports"]
                print(("RDS Aurora Cluster {} logs {} are enabled to exports to cloudwatch" \
                      .format(id,logs_exports_to_cloudwatch)))
        else:
              print("db_engine valid options are: mysql or aurora")
              exit()
    except Exception as e:
        print(e) 

if __name__=="__main__":

    parser =  argparse.ArgumentParser()
    parser.add_argument('--db_engine', help='RDS engine: mysql or aurora',required=True)
    parser.add_argument('--db_identifier', help='RDS instance ID',required=True)
    parser.add_argument('--logs_to_publish',help='Logs to export to cloudwatch',default='error')

    args = parser.parse_args()
    publish_rds_logs_to_cloudwatch(args.db_engine,args.db_identifier,args.logs_to_publish)
