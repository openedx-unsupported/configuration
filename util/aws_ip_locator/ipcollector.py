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
        if entry.has_key(external_hostnames_key):
            external_hostnames = entry[external_hostnames_key]
            for hostname in external_hostnames:
                print_line_item(hostname, get_ip_for_hostname(hostname))

        internal_hostnames_key = 'ec2_name_tags'
        if entry.has_key(internal_hostnames_key):
            internal_name_tags = entry[internal_hostnames_key]
            for pair in internal_name_tags:
                display_name = pair['display_name']
                aws_tag_name = pair['aws_tag_name']
                ip = get_instance_ip_by_name_tag(aws_tag_name)
                print_line_item(display_name, ip)

        elasticache_clusters_key = 'elasticache_clusters'
        if entry.has_key(elasticache_clusters_key):
            elasticache_clusters = entry[elasticache_clusters_key]
            for cluster in elasticache_clusters:
                display_name = cluster['display_name']
                cluster_id   = cluster['cluster_id']
                print_line_item(display_name, get_elasticache_ip_by_cluster_id(cluster_id))

        rds_instances_key = 'rds_instances'
        if entry.has_key(rds_instances_key):
            rds_instances = entry[rds_instances_key]
            for instance in rds_instances:
                display_name = instance['display_name']
                instance_id   = instance['instance_id']
                print_line_item(display_name, get_rds_ip_by_instance_id(instance_id))


cli.add_command(collect_ips)

def get_ip_for_hostname(hostname):
    return socket.gethostbyname(hostname)

def print_header(name):
    header ="""
============================
{0}
============================"""
    print(header.format(name))

def print_line_item(target, ip):
    line = "[ * ] {0} - {1}"
    print(line.format(target, ip))

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

def get_rds_ip_by_instance_id(instance_id):
    client = boto3.client('rds')
    response = client.describe_db_instances(
        DBInstanceIdentifier=instance_id,
    )
    hostname = response['DBInstances'][0]['Endpoint']['Address']
    return get_ip_for_hostname(hostname)

if __name__ == '__main__':
    cli()
