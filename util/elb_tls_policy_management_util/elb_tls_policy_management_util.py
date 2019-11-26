from __future__ import absolute_import
from __future__ import print_function
import boto3
import click
import datetime

elb_client = None


@click.group()
def cli():
    pass


def get_client():
    global elb_client
    if elb_client is None:
        elb_client = boto3.client('elb')
    return elb_client


def get_policies():
    client = get_client()
    response = client.describe_load_balancer_policies()
    policy_infos = response['PolicyDescriptions']
    return policy_infos


def get_tls_security_policy_template_names():
    policy_infos = get_policies()
    policy_template_names = list()

    for policy_info in policy_infos:
        if policy_info['PolicyTypeName'] == 'SSLNegotiationPolicyType':
            policy_template_names.append(policy_info['PolicyName'])

    return policy_template_names


def check_valid_policy(ctx, param, value):
    list_of_valid_policy_names = get_tls_security_policy_template_names()
    if value not in list_of_valid_policy_names:
        raise click.BadParameter("""Could not find the specified policy version,
                                 found versions: {0}"""
                                 .format(list_of_valid_policy_names))
    return value


def get_elb_infos():
    client = get_client()
    client.describe_load_balancers()
    response = client.describe_load_balancers(
        PageSize=400
    )
    return response['LoadBalancerDescriptions']


def get_elb_names():
    elb_names = list()
    for elb_info in get_elb_infos():
        elb_names.append(elb_info['LoadBalancerName'])
    return elb_names


def print_header(header):
    print("\n\n----------------------------------------------")
    print(("[   ] {0}".format(header)))
    print("----------------------------------------------")


def print_line_item(line_item):
    print(("[ * ] {0}".format(line_item)))


def print_list(name, items_list):
    print_header(name)
    for item in items_list:
        print_line_item(item)


def create_tls_policy(elb_name, policy_version_to_copy):
    client = get_client()
    policy_attributes = list()
    # AWS will copy all the other attributes.
    policy_attributes.append({
        "AttributeName": "Reference-Security-Policy",
        "AttributeValue": policy_version_to_copy
    })
    milli_datetime = str(int(datetime.datetime.now().strftime("%s")) * 1000)
    print('Creating new policy for elb....')
    new_policy_name = "SSLUpdateScript-SSLNegotiationPolicy-{0}-{1}".format(
        elb_name, milli_datetime)
    response = client.create_load_balancer_policy(
        LoadBalancerName=elb_name,
        PolicyName=new_policy_name,
        PolicyTypeName='SSLNegotiationPolicyType',
        PolicyAttributes=policy_attributes
    )
    print('Done creating ...')
    return new_policy_name


def elb_ref_policy(elb_name, policy_names):
    ref_policies = list()
    client = get_client()

    response = client.describe_load_balancer_policies(
        LoadBalancerName=elb_name,
        PolicyNames=policy_names
    )

    policies = response['PolicyDescriptions']
    for policy in policies:
        if policy['PolicyTypeName'] == 'SSLNegotiationPolicyType':
            for attribute in policy['PolicyAttributeDescriptions']:
                if attribute['AttributeName'] == 'Reference-Security-Policy':
                    ref_policies.append(attribute['AttributeValue'])
    return ref_policies


def get_reference_templates(elb_name):
    client = get_client()
    listener_descriptions = client.describe_load_balancers(
        LoadBalancerNames=[
            elb_name,
        ],
    )['LoadBalancerDescriptions'][0]['ListenerDescriptions']
    reference_security_policies = list()
    for listener_description in listener_descriptions:
        if listener_description['Listener']['Protocol'] == 'HTTPS':
            policy_names = listener_description['PolicyNames']
            elb_reference_policies = elb_ref_policy(elb_name, policy_names)
            reference_security_policies.extend(elb_reference_policies)
    return reference_security_policies


@click.command()
def show_available_policy_versions():
    list_of_valid_policy_names = get_tls_security_policy_template_names()
    print_list('Available Policies: ', list_of_valid_policy_names)


@click.command()
def show_elb_policy_versions():
    print('\n Please be patient.. this may take a moment...\n\n')
    elb_infos = get_elb_infos()
    elbs_by_current_policy = {}
    for elb_info in elb_infos:
        elb_name = elb_info['LoadBalancerName']
        reference_templates = get_reference_templates(elb_name)
        for reference_template in reference_templates:
            if reference_template not in elbs_by_current_policy:
                elbs_by_current_policy[reference_template] = []
            elbs_by_current_policy[reference_template].append(elb_name)
    for policy_name in elbs_by_current_policy.keys():
        print_list(policy_name, elbs_by_current_policy[policy_name])
    print('\n\n')


@click.command()
@click.option('--policy_version', callback=check_valid_policy,
              help='The TLS Policy version you would like to set',
              required=True)
@click.option('--names',
              required=False,
              help="""
              Comma separated ELB names eg:
              'elb-name-app1,elb-name-app1'.
              This field is case sensitive.""")
@click.option('--port_override',
              required=False,
              default=None,
              help="""
              Force the tls updater to only pay attention to a specific port
              By default it will find the correct port and do the right thing
              this only matters if you have multiple tls listeners on different
              ports""")
@click.option('--confirm', default=False, required=False, is_flag=True,
              help='Set this when you actually want to do the update.')
def update_elb_policies(confirm, policy_version, names, port_override):
    elb_names = get_elb_names()
    elb_names_to_update = []

    if names is not None:
        names = names.replace(' ', '').split(',')
        for name in names:
            if name in elb_names:
                elb_names_to_update.append(name)
    else:
        raise Exception('You must specify names...')

    elb_names_to_update = set(elb_names_to_update)

    if confirm is False:
        print('\n\nIf I actually ran the update this would be the result:\n')

    if confirm is False:
        print_list(policy_version, elb_names_to_update)
        print('\nAppend --confirm to actually perform the update\n')
    else:
        for elb_name in elb_names_to_update:
            tls_policy_name = create_tls_policy(elb_name, policy_version)
            print(("Trying to update...{0}".format(elb_name)))
            client = get_client()

            # Determine which policies are actually active
            # on the ELB on the 443 listener,
            # as AWS has all policies that have
            # ever been active on the ELB in their policies endpoint
            elbs = client.describe_load_balancers(
                LoadBalancerNames=[
                    elb_name,
                ],
            )['LoadBalancerDescriptions']

            load_balancer_descriptions = list()
            for elb in elbs:
                if(elb['LoadBalancerName'] == elb_name):
                    load_balancer_descriptions.append(elb)

            load_balancer_description = load_balancer_descriptions[0]

            listeners = load_balancer_description['ListenerDescriptions']
            
            active_policy_names = list()
            tls_port = None
            for listener in listeners:
                if((port_override is not None and listener['Listener']['LoadBalancerPort'] == int(port_override)) or (port_override is None and listener['Listener']['Protocol'] == 'HTTPS')):
                    tls_port = listener['Listener']['LoadBalancerPort']
                    active_policy_names.extend(listener['PolicyNames'])
                    break

            if(tls_port is None and port_override is not None):
                print("""Skipped updating this ELB because it does not have a listener
                on the specified override port\n""")
                continue
            
            # Now remove the active TLS related policy from that list,
            # this requires querying a different endpoint
            # as there is no way to know which policies are active
            # from the following endpoint:
            policies = client.describe_load_balancer_policies(
                LoadBalancerName=elb_name
            )['PolicyDescriptions']

            # Make a new list containing the new TLS policy,
            # and any previously active policies that are not TLS policies

            non_tls_policies = list()

            for policy in policies:
                if policy['PolicyTypeName'] != 'SSLNegotiationPolicyType':
                    non_tls_policies.append(policy)

            non_tls_policy_names = list()
            for non_tls_policy in non_tls_policies:
                non_tls_policy_names.append(non_tls_policy['PolicyName'])

            non_tls_policies_on_listener = list()

            for policy_name in active_policy_names:
                if(policy_name in non_tls_policy_names):
                    non_tls_policies_on_listener.append(policy_name)

            policy_names = non_tls_policies_on_listener + [tls_policy_name]
            response = client.set_load_balancer_policies_of_listener(
                LoadBalancerName=elb_name,
                LoadBalancerPort=tls_port,
                PolicyNames=policy_names
            )
            print(("Updated {0}\n".format(elb_name)))

cli.add_command(show_available_policy_versions)
cli.add_command(show_elb_policy_versions)
cli.add_command(update_elb_policies)

if __name__ == '__main__':
    cli()
