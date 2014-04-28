#!/usr/bin/env python
import boto
import boto.route53
import boto.route53.record
import boto.ec2.elb
import boto.rds2
import time
from argparse import ArgumentParser, RawTextHelpFormatter
import datetime
import sys
from vpcutil import rds_subnet_group_name_for_stack_name, all_stack_names

description = """

   Creates a new RDS instance in a VPC using restore
   from point in time using the latest available backup.
   The new db will be the same size as the original.
   The name of the db will remain the same, the master db password
   will be changed and is set on the command line.

   New db name defaults to "from-snapshot-<source db name>-<date>"
   A new DNS entry will be created for the RDS when provided
   on the command line

"""

RDS_SIZES = [
    'db.m1.small',
    'db.m1.large',
    'db.m1.xlarge',
    'db.m2.xlarge',
    'db.m2.2xlarge',
    'db.m2.4xlarg',
]


def parse_args(args=sys.argv[1:]):

    stack_names = all_stack_names()
    rds = boto.rds2.connect_to_region('us-east-1')
    dbs = [db['DBInstanceIdentifier']
           for db in rds.describe_db_instances()['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances']]

    parser = ArgumentParser(description=description, formatter_class=RawTextHelpFormatter)
    parser.add_argument('-s', '--stack-name', choices=stack_names,
                        default='stage-edx',
                        help='Stack name for where you want this RDS instance launched')
    parser.add_argument('-t', '--type', choices=RDS_SIZES,
                        default='db.m1.small', help='RDS size to create instances of')
    parser.add_argument('-d', '--db-source', choices=dbs,
                        default=u'stage-edx', help="source db to clone")
    parser.add_argument('-p', '--password', required=True,
                        help="password for the new database", metavar="NEW PASSWORD")
    parser.add_argument('-r', '--region', default='us-east-1',
                        help="region to connect to")
    return parser.parse_args(args)


def wait_on_db_status(db_name, region='us-east-1', wait_on='available', aws_id=None, aws_secret=None):
    rds = boto.rds2.connect_to_region(region)
    while True:
        statuses = rds.describe_db_instances(db_name)['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances']
        if len(statuses) > 1:
            raise Exception("More than one instance returned for {0}".format(db_name))
        if statuses[0]['DBInstanceStatus'] == wait_on:
            break
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(2)
    return

if __name__ == '__main__':
    # restore_db_instance_to_point_in_time(source_db_instance_identifier, target_db_instance_identifier, restore_time=None, use_latest_restorable_time=None, db_instance_class=None, port=None, availability_zone=None, db_subnet_group_name=None, multi_az=None, publicly_accessible=None, auto_minor_version_upgrade=None, license_model=None, db_name=None, engine=None, iops=None, option_group_name=None, tags=None)
    args = parse_args()

    rds = boto.rds2.connect_to_region(args.region)
    subnet_name = rds_subnet_group_name_for_stack_name(args.stack_name)
    restore_dbid = 'from-{0}-{1}-{2}'.format(args.db_source, datetime.date.today(), int(time.time()))
    rds.restore_db_instance_to_point_in_time(
        source_db_instance_identifier=args.db_source,
        target_db_instance_identifier=restore_dbid,
        use_latest_restorable_time=True,
        db_instance_class=args.type,
        db_subnet_group_name=subnet_name)
    wait_on_db_status(restore_dbid)
    #rds.modify_db_instance(restore_dbid, master_password=args.password)
