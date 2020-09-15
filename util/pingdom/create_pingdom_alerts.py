from __future__ import absolute_import
from __future__ import print_function
import json
import click
import yaml
import requests

import json
from six.moves import map


class PingdomInvalidResponse(Exception):
    pass


@click.command()
@click.option('--noop', is_flag=True, help="Don't apply changes to Pingdom.")
@click.option('--pingdom-email', required=True,
              help='Email to use to speak with Pingdom.',
              envvar='PINGDOM_EMAIL')
@click.option('--pingdom-password', required=True,
              help='Password to use to speak with Pingdom.',
              envvar='PINGDOM_PASSWORD')
@click.option('--pingdom-api-key', required=True,
              help='API Key to use to speak with Pingdom.',
              envvar='PINGDOM_API_KEY')
@click.option('--alert-config-file', required=True,
              help="path to config file",
              envvar='ALERT_CONFIG_FILE')
def main(noop, pingdom_email, pingdom_password,
         pingdom_api_key,
         alert_config_file):
    with open(alert_config_file, 'r') as stream:
        config_file_content = yaml.safe_load(stream)
    config_file_content = replace_user_names_with_userids(pingdom_email,
                                                          pingdom_password,
                                                          pingdom_api_key,
                                                          config_file_content)

    config_file_content = integration_names_to_ids(config_file_content)
    check_for_update, checks_by_hostname = build_checks_by_hostname(pingdom_email,
                                                  pingdom_password,
                                                  pingdom_api_key)
    for alert_config in config_file_content['checks']:
        if (alert_config['name'], alert_config['host']) not in checks_by_hostname.items():
            # Create new check
            if noop:
                print(("Would CREATE: {0}, but you set the noop flag.".format(
                    alert_config)))
            else:
                print(("CREATE: {0}".format(alert_config)))
                create_check(pingdom_email, pingdom_password,
                             pingdom_api_key, alert_config)

        else:
            # Updating existing check
            existing_check = check_for_update[alert_config['name']]
            if noop:
                print(("""
                Has changes, would UPDATE: {0},
                but you set the noop flag.
                """.format(alert_config)))
            else:
                print(("Attempting UPDATE: {0}".format(alert_config)))
                # We always update because the parameters to POST check
                # and the paramters returned by GET check differ.
                # It would be difficult to figure out if changes
                # have occured.
                update_check(pingdom_email, pingdom_password,
                             pingdom_api_key, existing_check['id'],
                             alert_config)


def replace_user_names_with_userids(pingdom_email,
                                    pingdom_password,
                                    pingdom_api_key,
                                    config_file_content):

    user_ids_by_name = build_userid_by_name(
        pingdom_email, pingdom_password, pingdom_api_key)
    for alert in config_file_content['checks']:
        user_ids = []
        if 'users' in alert:
            for user in alert['users']:
                if 'userids' in alert:
                    user_ids.extend(
                        [x.strip() for x in alert['userids'].split(',')])
                if user not in user_ids_by_name:
                    raise PingdomInvalidResponse(
                        'Pingdom has no user with the name {0}'.format(user))
                user_id = user_ids_by_name[user]
                user_ids.append(user_id)
            del alert['users']
            alert['userids'] = ','.join(map(str, user_ids))
    return config_file_content


def integration_names_to_ids(config_file_content):
    integration_ids_by_name = config_file_content['integration_name_to_id_map']
    for alert in config_file_content['checks']:
        integration_ids = []
        if 'integrations' in alert:
            for integration in alert['integrations']:
                if('integrationids' in alert):
                    integration_ids.extend(
                        alert['integrationids'].split(','))
                if integration not in list(integration_ids_by_name.keys()):
                    print(
                        """
                        You specified a integration
                        that does not exist in
                        our map.
                        """)
                    print(
                        """
                        You may just need to add it to the
                        build_integrations_by_name method
                        pingdom does not have an API for this presently...
                        """)
                    exit(1)
                integration_id = integration_ids_by_name[integration]
                integration_ids.append(integration_id)
                del alert['integrations']
                alert['integrationids'] = ','.join(map(str, integration_ids))
    return config_file_content


def create_check(pingdom_email, pingdom_password, pingdom_api_key, payload):
    try:
        response = requests.post("https://api.pingdom.com/api/2.1/checks",
                                 headers={
                                  'app-key': pingdom_api_key
                                 },
                                 auth=(pingdom_email, pingdom_password),
                                 params=payload)
        response.raise_for_status()
        print("Create successful")
    except requests.exceptions.HTTPError:
        print_error_prefix()
        print_request_and_response(response)
        exit(1)
    return json.loads(response.content.decode('utf-8'))


def update_check(pingdom_email, pingdom_password,
                 pingdom_api_key, id, payload):
    if('type' in payload):
        del(payload['type'])
    try:
        url = "https://api.pingdom.com/api/2.1/checks/{0}".format(id)
        response = requests.put(url,
                                headers={
                                    'app-key': pingdom_api_key
                                },
                                auth=(pingdom_email, pingdom_password),
                                params=payload)
        response.raise_for_status()
        print("Update successful")
    except requests.exceptions.HTTPError:
        print_error_prefix()
        print_request_and_response(response)
        exit(1)
    return json.loads(response.content.decode('utf-8'))


def list_checks(pingdom_email, pingdom_password, pingdom_api_key):
    try:
        response = requests.get("https://api.pingdom.com/api/2.1/checks",
                                headers={
                                    'app-key': pingdom_api_key
                                },
                                auth=(pingdom_email, pingdom_password))
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        print_error_prefix()
        print_request_and_response(response)
        exit(1)
    return json.loads(response.content.decode('utf-8'))['checks']


def list_users(pingdom_email, pingdom_password, pingdom_api_key):
    try:
        response = requests.get("https://api.pingdom.com/api/2.1/users",
                                headers={
                                    'app-key': pingdom_api_key
                                },
                                auth=(pingdom_email, pingdom_password))
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        print_error_prefix()
        print_request_and_response(response)
        exit(1)
    return json.loads(response.content.decode('utf-8'))


def build_checks_by_hostname(pingdom_email, pingdom_password, pingdom_api_key):
    checks = list_checks(pingdom_email, pingdom_password, pingdom_api_key)
    checks_by_hostname = {}
    check_for_update = {}
    for check in checks:
        check_for_update[str(check['name'])] = check
        checks_by_hostname[str(check['name'])] = str(check['hostname'])
    return check_for_update, checks_by_hostname


def build_userid_by_name(pingdom_email, pingdom_password, pingdom_api_key):
    user_content = list_users(
        pingdom_email, pingdom_password, pingdom_api_key)
    users = user_content['users']
    user_ids_by_name = {}
    for user in users:
        user_ids_by_name[user['name'].strip()] = user['id']
    return user_ids_by_name


def print_request_and_response(response):
    print("Request:")
    for key in response.request.headers:
        print(("{0}: {1}".format(key, response.request.headers[key])))
    print("")
    print((response.request.body))
    print("------------------")
    print("Response:")
    for key in response.headers:
        print(("{0}: {1}".format(key, response.headers[key])))
    print("")
    print((response.content.decode('utf-8')))
    print("------------------")


def print_error_prefix():
    print("Got error from pingdom, dumping request/response:")


if __name__ == "__main__":
    main()
