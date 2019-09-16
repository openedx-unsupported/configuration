from __future__ import absolute_import
from __future__ import print_function
import boto3
import click
import socket
import json

@click.group()
def cli():
    pass

@click.command()
@click.option('--file_name',
              required=True,
              help="""
              file containing tags name etc that you would like to find ips for, see examples for an example of this input""")
def collect_ips(file_name):
    output_json = json.load(open(file_name))

    for entry in output_json:
        print_header(entry['title'])

        external_hostnames_key = 'external_hostnames'
        if external_hostnames_key in entry:
            external_hostnames = entry[external_hostnames_key]
            for hostname in external_hostnames:
                print_line_item(hostname, get_ip_for_hostname(hostname))

        ec2_instance_name_tags_key = 'ec2_instance_name_tags'
        if ec2_instance_name_tags_key in entry:
            ec2_name_tags = entry[ec2_instance_name_tags_key]
            for pair in ec2_name_tags:
                display_name = pair['display_name']
                aws_tag_name = pair['aws_tag_name']
                ip = get_instance_ip_by_name_tag(aws_tag_name)
                print_line_item(display_name, ip)

        ec2_elb_name_tags_key = 'ec2_elb_name_tags'
        if ec2_elb_name_tags_key in entry:
            ec2_elb_name_tags = entry[ec2_elb_name_tags_key]
            for pair in ec2_elb_name_tags:
                display_name = pair['display_name']
                elb_name = pair['elb_name']
                ip = get_elb_ip_by_elb_name(elb_name)
                print_line_item(display_name, ip)

        elasticache_clusters_key = 'elasticache_clusters'
        if elasticache_clusters_key in entry:
            elasticache_clusters = entry[elasticache_clusters_key]
            for cluster in elasticache_clusters:
                display_name = cluster['display_name']
                cluster_id   = cluster['cluster_id']
                print_line_item(display_name, get_elasticache_ip_by_cluster_id(cluster_id))

        rds_instances_key = 'rds_instances'
        if rds_instances_key in entry:
            rds_instances = entry[rds_instances_key]
            for instance in rds_instances:
                display_name = instance['display_name']
                instance_id = None
                if 'instance_id' in instance:
                    instance_id   = instance['instance_id']
                    print_line_item(display_name, get_rds_ip_by_instance_id(instance_id))
                elif 'cluster_id' in instance:
                    cluster_id    = instance['cluster_id']
                    instance_id   = get_writer_instance_id_by_cluster_id(cluster_id)
                    print_line_item(display_name, get_rds_ip_by_instance_id(instance_id))
                else:
                    raise ValueError('Cant locate RDS instance without instance_id or cluster_id')

        static_entries_key = 'static_entries'
        if static_entries_key in entry:
            static_entries = entry[static_entries_key]
            for item in static_entries:
                display_name = item['display_name']
                display_value = item['display_value']
                print_line_item(display_name, display_value)


cli.add_command(collect_ips)

def get_ip_for_hostname(hostname):
    return socket.gethostbyname(hostname)

def print_header(name):
    header ="""
============================
{0}
============================"""
    print((header.format(name)))

def print_line_item(target, ip):
    line = "[ * ] {0} - {1}"
    print((line.format(target, ip)))

def get_instance_ip_by_name_tag(value):
    client = boto3.client('ec2')
    filters = [{  
        'Name': 'tag:Name',
        'Values': [value]
    }]

    response = client.describe_instances(Filters=filters)

    for r in response['Reservations']:
      for i in r['Instances']:
        if(i['State']['Name'] == 'running'):
            ip = i['PrivateIpAddress']
            return ip

def get_elb_ip_by_elb_name(elb_name):
    client = boto3.client('elb')
    response = client.describe_load_balancers(
        LoadBalancerNames=[
            elb_name,
        ]
    )
    hostname = response['LoadBalancerDescriptions'][0]['DNSName']
    return get_ip_for_hostname(hostname)

def get_elasticache_ip_by_cluster_id(cluster_id):
    client = boto3.client('elasticache')
    response = client.describe_cache_clusters(
        CacheClusterId=cluster_id,
        ShowCacheNodeInfo=True,
    )
    hostname = response['CacheClusters'][0]['CacheNodes'][0]['Endpoint']['Address']
    return get_ip_for_hostname(hostname)


def get_elasticache_ip_by_cluster_id(cluster_id):
    client = boto3.client('elasticache')
    response = client.describe_cache_clusters(
        CacheClusterId=cluster_id,
        ShowCacheNodeInfo=True,
    )
    hostname = response['CacheClusters'][0]['CacheNodes'][0]['Endpoint']['Address']
    return get_ip_for_hostname(hostname)

def get_writer_instance_id_by_cluster_id(cluster_id):
    client = boto3.client('rds')
    response = client.describe_db_clusters(
        DBClusterIdentifier=cluster_id
    )
    members = response['DBClusters'][0]['DBClusterMembers']
    for member in members:
        if member['IsClusterWriter']:
            return member['DBInstanceIdentifier']
    raise ValueError('Could not locate RDS instance with given instance_id or cluster_id')

def get_rds_ip_by_instance_id(instance_id):
    client = boto3.client('rds')
    response = client.describe_db_instances(
        DBInstanceIdentifier=instance_id,
    )
    hostname = response['DBInstances'][0]['Endpoint']['Address']
    return get_ip_for_hostname(hostname)

if __name__ == '__main__':
    cli()
