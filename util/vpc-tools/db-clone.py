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
import os

description = """

   Creates a new RDS instance in a VPC using restore
   from point in time using the latest available backup.
   The new db will be the same size as the original.
   The name of the db will remain the same, the master db password
   will be changed and is set on the command line.

   New db name defaults to "from-<source db name>-<human date>-<ts>"
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

# These are the groups for the different
# stack names that will be assigned once
# the corresponding db is cloned

SG_GROUPS = {
    'stage-edx': 'sg-d2f623b7',
}

# This group must already be created
# and allows for full access to port
# 3306. this group is assigned temporarily
# for cleaning the db

SG_GROUPS_FULL = {
    'stage-edx': 'sg-0abf396f',
}


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
    parser.add_argument('-p', '--password',
                        help="password for the new database", metavar="NEW PASSWORD")
    parser.add_argument('-r', '--region', default='us-east-1',
                        help="region to connect to")
    parser.add_argument('--dns',
                        help="dns entry for the new rds instance")
    parser.add_argument('--security-group', action="store_true",
                        default=False,
                        help="add sg group from SG_GROUPS")
    parser.add_argument('--clean', action="store_true",
                        default=False,
                        help="clean the db after launching it into the vpc, removing sensitive data")
    parser.add_argument('--dump', action="store_true",
                        default=False,
                        help="create a sql dump after launching it into the vpc")
    parser.add_argument('--secret-var-file',
                        help="using a secret var file run ansible against the host to update db users")

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
    args = parse_args()
    sanitize_sql_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "sanitize-db.sql")
    play_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../playbooks/edx-east")

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

    db_host = rds.describe_db_instances(restore_dbid)['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances'][0]['Endpoint']['Address']

    if args.password or args.security_group:
        modify_args = dict(
            apply_immediately=True
        )
        if args.password:
            modify_args['master_user_password'] = args.password
        if args.security_group:
            modify_args['vpc_security_group_ids'] = [SG_GROUPS[args.stack_name], SG_GROUPS_FULL[args.stack_name]]

        # Update the db immediately
        rds.modify_db_instance(restore_dbid, **modify_args)

    if args.clean:
        # Run the mysql clean sql file
        sanitize_cmd = """mysql -u root -p{root_pass} -h{db_host} < {sanitize_sql_file} """.format(
            root_pass=args.password,
            db_host=db_host,
            sanitize_sql_file=sanitize_sql_file)
        print("Running {}".format(sanitize_cmd))
        os.system(sanitize_cmd)

    if args.secret_var_file:
        db_cmd = """cd {play_path} && ansible-playbook -c local -i 127.0.0.1, update_edxapp_db_users.yml """ \
            """-e @{secret_var_file} -e "edxapp_db_root_user=root edxapp_db_root_pass={root_pass} """ \
            """EDXAPP_MYSQL_HOST={db_host}" """.format(
            root_pass=args.password,
            secret_var_file=args.secret_var_file,
            db_host=db_host,
            play_path=play_path)
        print("Running {}".format(db_cmd))
        os.system(db_cmd)

    if args.dns:
        dns_cmd = """cd {play_path} && ansible-playbook -c local -i 127.0.0.1, create_cname.yml """ \
            """-e "dns_zone=edx.org dns_name={dns} sandbox={db_host}" """.format(
            play_path=play_path,
            dns=args.dns,
            db_host=db_host)
        print("Running {}".format(dns_cmd))
        os.system(dns_cmd)

    if args.security_group:
        # remove full mysql access from within the vpc
        rds.modify_db_instance(restore_dbid, vpc_security_group_ids=[SG_GROUPS[args.stack_name]])
