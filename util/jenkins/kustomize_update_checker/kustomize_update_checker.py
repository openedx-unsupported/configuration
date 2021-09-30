#!/usr/bin/env python
import subprocess
import yaml
import sys
import logging
import click
import boto3
import backoff
from botocore.exceptions import ClientError


LOGGER = logging.getLogger(__name__)
logging.basicConfig()
global_list = []
MAX_TRIES = 5


class SESBotoWrapper:
    def __init__(self, **kwargs):
        self.client = boto3.client("ses", **kwargs)

    @backoff.on_exception(backoff.expo,
                          ClientError,
                          max_tries=MAX_TRIES)
    def send_email(self, *args, **kwargs):
        return self.client.send_email(*args, **kwargs)


def parse_yaml(file_name):
    with open(file_name, 'r') as stream:
        try:
            apps_details = yaml.safe_load(stream)
            for item in apps_details:
                registery = apps_details[item]["registery"]
                repo = apps_details[item]["repo"]
                url = "https://" + registery + "/v1/repositories/" + repo + "/tags"
                sed_filter = "sed -e 's/[][]//g' -e 's/\"//g' -e 's/ //g' | tr '}' '\n'  | awk -F: '{print $3}' | tail -1"
                cmd = "wget -q " + url + " -O -  | " + sed_filter
                latest_version = subprocess.check_output(cmd, shell=True).strip().decode("utf-8")
                check_version(item, apps_details[item]["version"], latest_version)

        except yaml.YAMLError as exc:
            LOGGER.error("error in configuration file: %s" % str(exc))
            sys.exit(1)
        except KeyError as e:
            print('I got a KeyError - reason "%s"' % str(e))


def check_version(app_name, app_version, latest_version):
    if not compare_version(app_version, latest_version):
        temp_dict = {
            app_name: {
                "current_version": app_version,
                "latest_version": latest_version
            },
        }
        global_list.append(temp_dict)


def compare_version(current_version, latest_version):
    if current_version == latest_version:
        return True
    return False


def send_an_email(to_addr, from_addr, app_list, region):
    ses_client = SESBotoWrapper(region_name=region)

    message = """
    <p>Hello,</p>
    <p>Updates are available for the following kustomize based apps</p>
    <table style='width:100%'>
      <tr style='text-align: left'>
        <th>App Name</th>
        <th>Current version</th>
        <th>Latest Version</th>
      </tr>
    """
    for apps in app_list:
        for data in apps:
            message += """
                <tr><td>{AppName}</td>
                <td>{CurrentVersion}</td>
                <td>{LatestVersion}</td>
                </tr>""".format(
                AppName=data,
                CurrentVersion=apps[data]["current_version"],
                LatestVersion=apps[data]["latest_version"]
            )

    message += """</table>"""
    print(("Sending the following as email to {}".format(to_addr)))
    print(message)
    ses_client.send_email(
        Source=from_addr,
        Destination={
            'ToAddresses': [
                to_addr
            ]
        },
        Message={
            'Subject': {
                'Data': 'Updates available for kustomize based apps',
                'Charset': 'utf-8'
            },
            'Body': {
                'Html':{
                    'Data': message,
                    'Charset': 'utf-8'
                }
            }
        }
    )


@click.command()
@click.option('--file-name', required=True, help='Filename which have kustomize based apps details.')
@click.option('--file-path', required=True, help='File path where kustomize based apps file exists.')
@click.option('--region', multiple=True, help='Default AWS region')
@click.option('--recipient', multiple=True, help='Recipient Email address')
@click.option('--sender', multiple=True, help='Sender email address')
def controller(file_name, file_path, region, recipient, sender):
    parse_yaml(file_name)
    if len(global_list) > 0:
        send_an_email(recipient[0], sender[0], global_list, region[0])


if __name__ == "__main__":
    controller()
