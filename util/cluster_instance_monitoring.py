from __future__ import absolute_import
from __future__ import print_function
import boto3
import argparse
import sys
import yaml
from pprint import pprint

def find_active_instances(cluster_file, region):
    """
    Determines if a given cluster has at least one ASG and at least one active instance.

    Input: 
    cluster_file: a yaml file containing a dictionary of triples that specify the particular cluster to monitor.
    The keys of each entry in the dictionary are 'env', 'deployment', and 'cluster', specifying the environment, deployment,
        and cluster to find ASG's and active instances for. 

    """
    with open(cluster_file, 'r') as f:
        cluster_map = yaml.safe_load(f)

    asg = boto3.client('autoscaling', region)
    all_groups = asg.describe_auto_scaling_groups(MaxRecords=100)

    # dictionary that contains the environment/deployment/cluster triple as the key and the value is a list of the asgs that match the triple
    all_matching_asgs = {}

    # all the triples for which an autoscaling group does not exist 
    not_matching_triples = []

    # check if there exists at least one ASG for each triple
    for triple in cluster_map:
        #the asgs that match this particular triple
        cluster_asgs = []
        
        for g in all_groups['AutoScalingGroups']:
            match_env = False
            match_deployment = False
            match_cluster = False
            for tag in g['Tags']:
                if tag['Key'] == 'environment' and tag['Value'] == triple['env']:
                    match_env = True
                if tag['Key'] == 'deployment' and tag['Value'] == triple['deployment']:
                    match_deployment = True
                if tag['Key'] == 'cluster' and tag['Value'] == triple['cluster']:
                    match_cluster = True
            if match_env and match_cluster and match_deployment:
                cluster_asgs += [g]
        
        if not cluster_asgs:
            not_matching_triples += [triple]
        else:
            triple_str = triple['env'] + '-' + triple['deployment'] + '-' + triple['cluster']
            all_matching_asgs[triple_str] = cluster_asgs

    #The triples that have no active instances
    no_active_instances_triples = []

    #check that each triple has at least one active instance in at least one of its ASG's
    for triple in all_matching_asgs:
        asgs = all_matching_asgs[triple]
        triple_has_active_instances = False
        for asg in asgs:
            for instance in asg['Instances']:
                if instance['LifecycleState'] == 'InService':
                    triple_has_active_instances = True
        if not triple_has_active_instances:
            no_active_instances_triples += [triple]


    if no_active_instances_triples or not_matching_triples:
        if not_matching_triples:
            print('Fail. There are no autoscaling groups found for the following cluster(s):')
            pprint(not_matching_triples)
        if no_active_instances_triples:
            print("Fail. There are no active instances for the following cluster(s)")
            for triple in no_active_instances_triples:
                print(('environment: ' + triple.split('-')[0]))
                print(('deployment: ' + triple.split('-')[1]))
                print(('cluster: ' + triple.split('-')[2]))
                print('----')
        sys.exit(1)
    
    print("Success. ASG's with active instances found for all of the cluster triples.")
    sys.exit(0)

    
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='Yaml file of env/deployment/cluster triples that we want to find active instances for', required=True)
    parser.add_argument('-r', '--region', help="Region that we want to find ASG's and active instances in", default='us-east-1', required=True)
    args = parser.parse_args()

    find_active_instances(args.file, args.region)

