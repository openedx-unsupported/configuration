import boto3
import argparse
import sys
import yaml
import pprint

def find_active_instances(cluster_file):
    """
    Determines if a given cluster has at least one ASG and at least one active instance.

    Input: 
    cluster_file: a yaml file containing a dictionary of triples that specify the particular cluster to monitor.
    The keys of each entry in the dictionary are 'env', 'deployment', and 'cluster', specifying the environment, deployment,
        and cluster to find ASG's and active instances for. 

    """
    pp = pprint.PrettyPrinter()

    f = open(cluster_file)
    cluster_map = yaml.safe_load(f)
    f.close()

    region = 'us-east-1'

    asg = boto3.client('autoscaling', region)
    all_groups = asg.describe_auto_scaling_groups()

    #all the asgs that match the specified environment, deployment, and cluster triples from the cluster map
    all_matching_asgs = []

    #all the triples for which an autoscaling group does not exist 
    not_matching_triples = []

    #check if there exists at least one ASG for each triple
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
            all_matching_asgs += cluster_asgs

    #The ASG's for the triples that have no active instances
    no_active_instances_asgs = []

    #check to make sure each ASG has at least 1 running instance
    for asg in all_matching_asgs:
        asg_has_active_instances = False
        for instance in asg['Instances']:
            if instance['LifecycleState'] == 'InService':
                asg_has_active_instances = True
                break
        if not asg_has_active_instances:
            no_active_instances_asgs += [asg]


    if no_active_instances_asgs or not_matching_triples:
        if not_matching_triples:
            print('Fail. There are no autoscaling groups found for the following cluster(s):')
            pp.pprint(not_matching_triples)
        if no_active_instances_asgs:
            print("Fail. There are no active instances for the following ASG's:")
            pp.pprint(no_active_instances_asgs)
        sys.exit(1)
    
    print("Success. ASG's with active instances found for all of the cluster triples.")
    sys.exit(0)

    
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='Yaml file of env/deployment/cluster triples that we want to find active instances for', required=True)
    args = parser.parse_args()

    find_active_instances(args.file)

