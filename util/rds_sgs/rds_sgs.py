#!/usr/bin/python3

from __future__ import absolute_import
from __future__ import print_function
import boto3
import click

@click.command()
@click.argument('mode', type=click.Choice(['by_db', 'by_sg']))
def command(mode):
    """
    MODES:

    by_db: List rules for all RDS instances and which security group(s) they come from

    by_sg: shows each security group and which RDS instances are using it
    """
    client = boto3.client('rds')
    ec2_client = boto3.client('ec2')
    dbs = client.describe_db_instances()
    dbs_by_sg = {}
    for db in dbs['DBInstances']:
        open_ports = {}
        sg_ids = [sg['VpcSecurityGroupId'] for sg in db['VpcSecurityGroups']]
        for sg_id in sg_ids:
            sg = ec2_client.describe_security_groups(GroupIds=[sg_id])['SecurityGroups'][0]
            sg_id_and_name = "{} ({})".format(sg_id, sg['GroupName'])
            if sg_id_and_name in dbs_by_sg:
                dbs_by_sg[sg_id_and_name].append(db['DBInstanceIdentifier'])
            else:
                dbs_by_sg[sg_id_and_name] = [db['DBInstanceIdentifier']]

            if mode == 'by_db':
                for permission in sg['IpPermissions']:
                    if permission['FromPort'] == permission['ToPort']:
                        ports = permission['FromPort']
                    else:
                        ports = "{}-{}".format(permission['FromPort'],permission['ToPort'])
                    for IpRange in permission['IpRanges']:
                        key = IpRange['CidrIp']
                        desc = sg['GroupName']
                        if 'Description' in IpRange:
                            desc = "{}|{}".format(desc, IpRange['Description'])

                        if ports in open_ports:
                            if key in open_ports[ports]:
                                open_ports[ports][key][sg_id] = desc
                            else:
                                open_ports[ports][key] = {sg_id: desc}
                        else:
                            open_ports[ports] = {key: {sg_id: desc}}
                    for UserIdGroupPair in permission['UserIdGroupPairs']:
                        source_sg_id = UserIdGroupPair['GroupId']
                        key = "{} ({})".format(source_sg_id, ec2_client.describe_security_groups(GroupIds=[source_sg_id])['SecurityGroups'][0]['GroupName'])

                        desc = sg['GroupName']
                        if 'Description' in UserIdGroupPair:
                            desc = "{}|{}".format(desc, UserIdGroupPair['Description'])

                        if ports in open_ports:
                            if key in open_ports[ports]:
                                open_ports[ports][key][sg_id] = desc
                            else:
                                open_ports[ports][key] = {sg_id: desc}
                        else:
                            open_ports[ports] = {key: {sg_id: desc}}

        for ports,sources in open_ports.items():
            for source in sorted(sources.keys()):
                sgs = []
                for sg_id in sorted(sources[source].keys()):
                    output = sg_id
                    if sources[source][sg_id]:
                        output = "{} ({})".format(output, sources[source][sg_id])
                    sgs.append(output)
                print(("{: <40} {: <11} {: <70} {}".format(db['DBInstanceIdentifier'], ports, source, ", ".join(sgs))))
    if mode == 'by_sg':
        for sg,dbs in dbs_by_sg.items():
            print(("{: <70} {: <4}  {}".format(sg, len(dbs), ", ".join(dbs))))

if __name__ == '__main__':
    command()
