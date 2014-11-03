#!/usr/bin/env python -u
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

   Creates a new RDS instance using restore
   from point in time using the latest available backup.
   The new db will be the same size as the original.
   The name of the db will remain the same, the master db password
   will be changed and is set on the command line.

   If stack-name is provided the RDS instance will be launched
   in the VPC that corresponds to that name.

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

def parse_args(args=sys.argv[1:]):

    stack_names = all_stack_names()
    rds = boto.rds2.connect_to_region('us-east-1')
    dbs = [db['DBInstanceIdentifier']
           for db in rds.describe_db_instances()['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances']]

    parser = ArgumentParser(description=description, formatter_class=RawTextHelpFormatter)
    parser.add_argument('--vpc', default=None, action="store_true",
                        help='this is for a vpc')
    parser.add_argument('--security-group', default=None,
                        help='security group name that should be assigned to the new RDS instance (vpc only!)')
    parser.add_argument('--subnet', default=None,
                        help='subnet that should be used for the RDS instance (vpc only!)')
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
    parser.add_argument('--clean-wwc', action="store_true",
                        default=False,
                        help="clean the wwc db after launching it into the vpc, removing sensitive data")
    parser.add_argument('--clean-prod-grader', action="store_true",
                        default=False,
                        help="clean the prod_grader db after launching it into the vpc, removing sensitive data")
    parser.add_argument('--dump', action="store_true",
                        default=False,
                        help="create a sql dump after launching it into the vpc")
    parser.add_argument('-s', '--secret-var-files', action="append", required=True,
                        help="use one or more secret var files to run ansible against the host to update db users")

    return parser.parse_args(args)


def wait_on_db_status(db_name, region='us-east-1', wait_on='available', aws_id=None, aws_secret=None):
    rds = boto.rds2.connect_to_region(region)
    while True:
        statuses = rds.describe_db_instances(db_name)['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances']
        if len(statuses) > 1:
            raise Exception("More than one instance returned for {0}".format(db_name))
        if statuses[0]['DBInstanceStatus'] == wait_on:
            print("Status is: {}".format(wait_on))
            break
        sys.stdout.write("status is {}..\n".format(statuses[0]['DBInstanceStatus']))
        sys.stdout.flush()
        time.sleep(10)
    return

if __name__ == '__main__':
    args = parse_args()
    sanitize_wwc_sql_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "sanitize-db-wwc.sql")
    sanitize_prod_grader_sql_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "sanitize-db-prod_grader.sql")
    play_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../playbooks/edx-east")

    rds = boto.rds2.connect_to_region(args.region)
    restore_dbid = 'from-{0}-{1}-{2}'.format(args.db_source, datetime.date.today(), int(time.time()))
    restore_args = dict(
        source_db_instance_identifier=args.db_source,
        target_db_instance_identifier=restore_dbid,
        use_latest_restorable_time=True,
        db_instance_class=args.type,
    )
    if args.vpc:
        restore_args['db_subnet_group_name'] = args.subnet
    rds.restore_db_instance_to_point_in_time(**restore_args)
    wait_on_db_status(restore_dbid)
    print("Getting db host")
    db_host = rds.describe_db_instances(restore_dbid)['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances'][0]['Endpoint']['Address']

    modify_args = dict(
        apply_immediately=True
    )
    if args.password:
        modify_args['master_user_password'] = args.password

    if args.vpc:
        modify_args['vpc_security_group_ids'] = [args.security_group]
    else:
        # dev-edx is the default security group for dbs that
        # are not in the vpc, it allows connections from the various
        # NAT boxes and from sandboxes
        modify_args['db_security_groups'] = ['dev-edx']

    # Update the db immediately
    print("Updating db instance: {}".format(modify_args))
    rds.modify_db_instance(restore_dbid, **modify_args)
    print("Waiting 15 seconds before checking to see if db is available")
    time.sleep(15)
    wait_on_db_status(restore_dbid)
    print("Waiting another 15 seconds")
    time.sleep(15)
    if args.clean_wwc:
        # Run the mysql clean sql file
        sanitize_cmd = """mysql -u root -p{root_pass} -h{db_host} wwc < {sanitize_wwc_sql_file} """.format(
            root_pass=args.password,
            db_host=db_host,
            sanitize_wwc_sql_file=sanitize_wwc_sql_file)
        print("Running {}".format(sanitize_cmd))
        os.system(sanitize_cmd)

    if args.clean_prod_grader:
        # Run the mysql clean sql file
        sanitize_cmd = """mysql -u root -p{root_pass} -h{db_host} prod_grader < {sanitize_prod_grader_sql_file} """.format(
            root_pass=args.password,
            db_host=db_host,
            sanitize_prod_grader_sql_file=sanitize_prod_grader_sql_file)
        print("Running {}".format(sanitize_cmd))
        os.system(sanitize_cmd)

    if args.secret_var_files:
        extra_args = ""
        for secret_var_file in args.secret_var_files:
            extra_args += " -e@{}".format(secret_var_file)

        db_cmd = """cd {play_path} && ansible-playbook -c local -i 127.0.0.1, create_dbs.yml """ \
            """{extra_args} -e "edxapp_db_root_user=root xqueue_db_root_user=root" """ \
            """ -e "db_root_pass={root_pass}" """ \
            """ -e "EDXAPP_MYSQL_HOST={db_host}" """ \
            """ -e "XQUEUE_MYSQL_HOST={db_host}" """.format(
            root_pass=args.password,
            extra_args=extra_args,
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
