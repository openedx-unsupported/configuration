#!/usr/bin/env python
import subprocess
import yaml
import sys
import logging
import click
import os
import json
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
            charts_name = yaml.safe_load(stream)
            if "dependencies" in charts_name:
                app_list = charts_name["dependencies"]
                for key in app_list:
                    add_helm(key["repository"], key["name"])
                update_helm()
                for key in app_list:
                    repo_name = get_repo_name(key["repository"])
                    check_version(charts_name["name"], key["name"], repo_name, key["version"])
        except yaml.YAMLError as exc:
            LOGGER.error("error in configuration file: %s" % str(exc))
            sys.exit(1)
        except KeyError as e:
            print(f"I got a KeyError - reason {str(e)}")


def add_helm(repo_url, repo_name):
    try:
        cmd_add = 'helm repo add ' + repo_name + " " + repo_url
        subprocess.check_output(cmd_add, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.output)


def update_helm():
    cmd_update = 'helm repo update'
    subprocess.check_output(cmd_update, shell=True)


def get_repo_name(repo_url):
    try:
        get_repo_cmd = 'helm repo list -o json'
        repositories = subprocess.check_output(get_repo_cmd, shell=True).strip()
        repo_list = json.loads(repositories.decode())
        for repo in repo_list:
            if repo["url"] == repo_url:
                return repo['name']
    except subprocess.CalledProcessError as e:
        print(e.output)


def check_version(chart_name, app_name, repo_name, app_version):
    cmd = 'helm show chart ' + repo_name + "/" + app_name + ' | grep version | tail -1'
    output = subprocess.check_output(cmd, shell=True)
    latest_version = output.decode().split(": ")[-1].rstrip()
    if not compare_version(app_version, latest_version):
        temp_dict = {
            chart_name+"/"+app_name: {
                "current_version": app_version,
                "latest_version": latest_version
            },
        }
        global_list.append(temp_dict)


def compare_version(current_version, latest_version):
    return True if current_version == latest_version else False


def find(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            parse_yaml(os.path.join(root, name))


def send_an_email(to_addr, from_addr, app_list, region):
    ses_client = SESBotoWrapper(region_name=region)

    message = """
    <p>Hello,</p>
    <p>Updates are available for the following helm charts</p>
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
                'Data': 'Updates available for helms charts',
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
@click.option('--file-name', required=True, help='Filename which have helm chart details.')
@click.option('--file-path', required=True, help='File path where helm chart file exists.')
@click.option('--region', multiple=True, help='Default AWS region')
@click.option('--recipient', multiple=True, help='Recipient Email address')
@click.option('--sender', multiple=True, help='Sender email address')
def controller(file_name, file_path, region, recipient, sender):
    find(file_name, file_path)
    if len(global_list) > 0:
        send_an_email(recipient[0], sender[0], global_list, region[0])


if __name__ == "__main__":
    controller()
