#!/usr/bin/env python
import boto, boto.route53, boto.rds2
import pymysql, yaml
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from datetime import datetime
import os, time, json, subprocess

description = """
   Creates a new RDS instance using restore
   from point in time using the latest available backup.
"""

def parse_args():
    parser = ArgumentParser(description=description, formatter_class=ArgumentDefaultsHelpFormatter)

    #Required args
    parser.add_argument('-s', '--source-db', dest='source_db', help="Identifier of RDS instance to clone (requried)", required=True)
    
    parser.add_argument('-n', '--subnet-group', dest='subnet', required=True,
                        help='RDS subnet group name that should be used for the RDS instance (required)')

    #Optional args
    parser.add_argument('-P', '--profile', dest='profile',
                        help='boto profile to use. Defaults to default boto profile.')

    parser.add_argument('-d', '--destination-db', dest='target_db', metavar='DEST_DB',
                        help=("identifier for new cloned RDS instance. Defaults to "
                        '"from-<source db id>-<year>-<month>-<day>-<hours>-<minutes>-<seconds>"'))
    #default gets set later so we can use args.source_db

    parser.add_argument('-u', '--user', dest='user', default='root',
                        help='master username to connect to the DB with')
    
    parser.add_argument('-p', '--password', dest='password',
                        help=("new master password for the new RDS instance. "
                        "If not set, the password will be unchanged."))
    
    parser.add_argument('-t', '--type', default='db.m3.medium', dest='instance_type', 
                        help='instance type to be used for clone')
    
    parser.add_argument('-o', '--option-group', default="default:mysql-5-6", dest='option_group',
                        help="RDS option group for the new instance.")
    
    parser.add_argument('-g', '--security-groups', nargs='+', dest='security_groups',
                        help='ids one or more security groups that should be assigned to the new RDS instance')
    
    parser.add_argument('-x', '--sql-script', action='append', nargs=2,
                        dest='sql_scripts', metavar=('DBNAME', 'SCRIPTFILE'),
                        help=("runs SCRIPTFILE (a SQL script) against DBNAME on the cloned instance. "
                        "This option can be specified multiple times for multiple scripts. "
                        "NB: if you don't specify --password, scripts can only be run "
                        "if the source instance has no password."))

    parser.add_argument('-c', '--dns', dest='dns', 
                        help="dns entry (CNAME) for the new instance (e.g. foo-bar.edx.org)")
    
    parser.add_argument('-f', '--db-file', dest='db_file',
                        help=("path to YAML file used for create_dbs_and_users play. "
                        "If not specified, no users/passwords other than the root one will be changed. "
                        'Note that the "database_connection" section of the file will be ignored.'))

    parser.add_argument('--skip-dbs', action='store_true', dest='ansible_skip_dbs',
                        help=("don't run the part of the create_dbs_and_users play that creates dbs. "
                        'Equivalent to "--skip-tags dbs"'))

    parser.add_argument('--skip-users', action='store_true', dest='ansible_skip_users',
                        help=("don't run the part of the create_dbs_and_users play that creates users. "
                        'Equivalent to "--skip-tags users"'))

    parser.add_argument('--ansible-venv', dest='ansible_venv', default="../../venv/bin/activate",
                        help="path to the virtualenv activate script that should be run before ansible is run")

    parser.add_argument('--create-dbs-and-users', dest='create_dbs_and_users',
                        default="../../playbooks/edx-east/create_db_and_users.yml",
                        help='path to the create_dbs_and_users.yml ansible play')
    

    args = parser.parse_args()
    if not args.target_db:
        args.target_db = 'from-{}-{:%Y-%m-%d-%H-%M-%S}'.format(args.source_db, datetime.now())

    return args


def wait_on_db_status(db_name, wait_on='available', wait_time=60):
    '''Block until RDS DB <db_name> reaches status <wait_on>.
    Args:
        db_name: Identifier of RDS instance
        rds: boto RDSConnection object
        wait_on: status to wait for
        wait_time: time in between retries
    '''
    while True:
        status = get_instance(db_name)['DBInstanceStatus']
        
        if status == wait_on:
            print 'Instance has reached status "{}"'.format(status)
            return
        else:
            print 'Waiting for instance to reach status "{}". Status is currently "{}".'.format(wait_on, status)
            time.sleep(wait_time)


def get_instance(db_name):
    '''Returns boto data about an instance
    Args:
        db_name: Identifier of an RDS instance
    '''
    instances = rds.describe_db_instances(db_name)['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances']
    
    #This shouldn't ever be True
    if len(instances) > 1:
        raise Exception("More than one instance returned for {0}".format(db_name))

    return instances[0]


def run_sql(host, user, password, db, script):
    '''Run a sql script file against a DB
    Args:
        host: hostname of an MySQL instance
        user: user to run the script as
        password: password to use
        db: database to use
        script: name of file containing SQL script to run
    '''
    print "Running {} against {}:{}".format(script, host, db)
    connection = pymysql.connect(host=host, database=db, user=user, password=password,
                                 cursorclass=pymysql.cursors.DictCursor)
    try:
        with open(script) as f:
            cur = connection.cursor()
            cur.execute(f.read())
            return cur.fetchall()
    finally:
        connection.close()
        print "Done"


def run_create_dbs_and_users(db_file, host, user, password, args):
    '''Run the create_dbs_and_users.yml ansible play
    Args:
        db_file: name of file containing data structure required by create_dbs_and_users
    '''
    print "Setting users and passwords per " + db_file
    
    play = os.path.basename(args.create_dbs_and_users)
    play_path = os.path.dirname(args.create_dbs_and_users)

    overrides = {
        'database_connection': {
            'login_host': host,
            'login_user': user,
            'login_password': password,
        }
    }

    skip_tags = ','.join(tag for flag,tag in 
        [[args.ansible_skip_users,'users'], [args.ansible_skip_dbs,'dbs']] if flag)

    cmd = "source {venv}; ansible-playbook -c local -i localhost, {play} -e@{dbfile} -e '{overrides}' {skiptags}".format(
        venv=args.ansible_venv, play=play, dbfile=db_file, overrides=json.dumps(overrides),
        skiptags=('--skip-tags ' + skip_tags) if skip_tags else '')
    
    sp = subprocess.Popen(cmd, shell=True, executable='/bin/bash', cwd=play_path, 
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while sp.poll() is None:
        print sp.stdout.read()

    if sp.returncode > 0:
        raise Exception(cmd + ' exited with status ' + str(sp.returncode))

    print "Done"


def add_cname(source, dest, wait_time=10):
    '''Add or overwrite a cname in Route53
    Args:
        source: CNAME points to this FQDN
        dest: FQDN of CNAME
    '''
    print "Adding CNAME from {} to {}".format(args.dns, dbhost)
    route53 = boto.connect_route53()
    
    domain = '.'.join(dest.split('.')[-2:])
    zone = route53.get_zone(domain)
    
    entry = zone.get_cname(dest)
    f = zone.update_cname if entry else zone.add_cname
    status = f(dest, source, ttl=300)
    
    while status.status != 'INSYNC':
        print 'Waiting for instance to reach status "{}". Status is currently "{}"'.format('INSYNC', status.status)
        status.update()
        time.sleep(wait_time)
    else:
        print "Route53 has updated"


def main():
    args = parse_args()

    global rds      #so we don't have to pass it into every function
    rds = boto.connect_rds2(profile_name=args.profile)

    ### Create Instance ###
    create_args = dict(
        source_db_instance_identifier = args.source_db,
        target_db_instance_identifier = args.target_db,
        use_latest_restorable_time = True,
        db_instance_class = args.instance_type,
        option_group_name = args.option_group,
        db_subnet_group_name = args.subnet,
    )
    
    print "Cloning instance: {}".format(create_args)
    rds.restore_db_instance_to_point_in_time(**create_args)

    wait_on_db_status(args.target_db)
    

    ### Set Instance Config ###    
    modify_args = dict(
        apply_immediately = True,
        master_user_password = args.password,
        vpc_security_group_ids = args.security_groups,
    )

    print "Updating db instance configuration: {}".format(modify_args)    
    rds.modify_db_instance(args.target_db, **modify_args)
    
    time.sleep(15)
    wait_on_db_status(args.target_db)
    time.sleep(15)


    ### Run SQL Scripts ###
    dbhost = get_instance(args.target_db)['Endpoint']['Address']
    if args.sql_scripts:
        for pair in args.sql_scripts:
            print run_sql(host=dbhost, user=args.user,
                password=args.password, db=pair[0], script=pair[1])


    ### Run create_dbs_and_users play to set users for desired target environment ###
    if args.db_file:
        run_create_dbs_and_users(args.db_file, dbhost, args.user, args.password, args)


    ### Create CNAME for new instance ###
    if args.dns:
        add_cname(dbhost, args.dns)


if __name__ == '__main__':
    main()
