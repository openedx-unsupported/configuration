from __future__ import absolute_import
from __future__ import print_function
import boto3
import requests
import click
from botocore.exceptions import ClientError
import sys
import re


class NewRelic:
    def __init__(self, new_relic_api_key):
        self.url_alert_extractor = "https://api.newrelic.com/v2/alerts_policies.json"
        self.headers = {'X-Api-Key': new_relic_api_key}

    def new_relic_policies_extractor(self):
        """
        Return:
             Return list of all alert policies extracted from New relic
             {
              "policy": {
                "id": int,
                "incident_preference": str,
                "name": str,
                "created_at": int,
                "updated_at": int
              }
            }
        """
        response = requests.get(self.url_alert_extractor, headers=self.headers)
        if response.status_code != 200:
            print("Unable to communicate with New relic.")
            sys.exit(1)
        try:
            alert_policies = response.json()
        except ValueError:
            print(("Failed to parse response json. Got:\n{}".format(response.text)))
            sys.exit(1)
        return alert_policies


class InfraAlerts:
    def edc_extractor(self):
        """
        Return list of all EC2 instances with EDC's tags across all the regions
        Returns:
            [
                {
                    'name': name,
                    'ID': instance.id
                }
            ]
        """
        client_region = boto3.client('ec2')
        filter_tags = [
                        {
                            "Name": "tag:environment",
                            "Values": ["*"]
                        },
                        {
                            "Name": "tag:deployment",
                            "Values": ["*"]
                        },
                        {
                            "Name": "tag:cluster",
                            "Values": ["*"]
                        },
                        {
                            'Name': 'instance-state-name',
                            'Values': ['running']
                        }
                      ]
        instance_list = []
        try:
            regions_list = client_region.describe_regions()
        except ClientError as e:
            print(("Unable to connect to AWS with error :{}".format(e)))
            sys.exit(1)
        for region in regions_list['Regions']:
            client = boto3.resource('ec2', region_name=region['RegionName'])
            response = client.instances.filter(Filters=filter_tags)
            for instance in response:
                temp_dict = {}
                for tag in instance.tags:
                    if tag['Key'] == "Name":
                        name = tag['Value']
                        temp_dict = {
                            'name': name,
                            'ID': instance.id
                        }
                        break
                    else:
                        pass
                instance_list.append(temp_dict)
        return instance_list

    def missing_alerts_checker(self, instance_list, alert_policies):
        """
        Arguments:
            instance_list (list):
                List of all instances for which we find alerts
            alert_policies list(dict):
                List of all existing alerts new relic
        Return:
            Return list of all instances which have no alert in new Relic
            [
                {
                    'name': name,
                    'ID': instance.id
                }
            ]
        """
        result_instance = []
        for instance in instance_list:
            if not any(policy["name"] == instance["name"] + "-infrastructure" for policy in alert_policies["policies"]):
                result_instance.append(instance)
        return result_instance


class AppAlerts:
    def __init__(self, new_relic_api_key):
        self.url_app_extractor = "https://api.newrelic.com/v2/applications.json"
        self.headers = {'X-Api-Key': new_relic_api_key}

    def new_relic_app_extractor(self):
        """
        Return:
             Return list all applications in new relic
        """
        response = requests.get(self.url_app_extractor, headers=self.headers)
        if response.status_code != 200:
            print("Unable to communicate with New relic.")
            sys.exit(1)
        try:
            apps_list = response.json()
        except ValueError:
            print(("Failed to parse response json. Got:\n{}".format(response.text)))
            sys.exit(1)
        return apps_list["applications"]

    def missing_alerts_checker(self, app_list, alert_policies):
        """
        Arguments:
            app_list (list):
                List of all applications for which we find alerts
            alert_policies list(dict):
                List of all existing alerts new relic
        Return:
            Return list of all applications which have no alert in new Relic
        """
        result_apps = []
        for apps in app_list:
            if not any(policy["name"] == apps["name"] + "-application" for policy in alert_policies["policies"]):
                result_apps.append(apps)
        return result_apps


class BrowserAlerts:
    def __init__(self, new_relic_api_key):
        self.url_browser_extractor = "https://api.newrelic.com/v2/browser_applications.json"
        self.headers = {'X-Api-Key': new_relic_api_key}

    def new_relic_browser_extractor(self):
        """
        Return:
             Return list all browser applications in new relic
              [
                  {
                    "id": "integer",
                    "name": "string",
                    "browser_monitoring_key": "string",
                    "loader_script": "string"
                  }
              ]
        """
        response = requests.get(self.url_browser_extractor, headers=self.headers)
        if response.status_code != 200:
            print("Unable to communicate with New relic.")
            sys.exit(1)
        try:
            browser_list = response.json()
        except ValueError:
            raise Exception("Failed to parse response json. Got:\n{}".format(response.text))
        return browser_list["browser_applications"]

    def missing_alerts_checker(self, browser_list, alert_policies):
        """
        Arguments:
            browser_list (list):
                List of all browser applications for which we find alerts
            alert_policies list(dict):
                List of all existing alerts new relic
        Return:
            Return list of all browser applications which have no alert in new Relic
            [
                  {
                    "id": "integer",
                    "name": "string",
                    "browser_monitoring_key": "string",
                    "loader_script": "string"
                  }
            ]
        """
        result_browser = []
        for browser in browser_list:
            if not any(policy["name"] == browser["name"].rstrip() + "-browser" for policy in alert_policies["policies"]):
                result_browser.append(browser)
        return result_browser


@click.command()
@click.option('--new-relic-api-key', required=True, help='API Key to use to speak with NewRelic.')
@click.option('--ignore', '-i', multiple=True, help='App name regex to filter out, can be specified multiple times')
def controller(new_relic_api_key,ignore):
    """
    Control execution of all other functions
    Arguments:
        new_relic_api_key (str):
            Get this from cli args
    """
    flag = 0
    # Initializing object of classes
    infracheck = InfraAlerts()
    new_relic_obj = NewRelic(new_relic_api_key)
    # Get list of all instances in different regions
    instance_list = infracheck.edc_extractor()
    # Get list of all alert policies in new relic
    alert_policies = new_relic_obj.new_relic_policies_extractor()
    # Get list of all instances without alerts
    missing_alerts_list = infracheck.missing_alerts_checker(instance_list, alert_policies)
    filtered_missing_alerts_list = list([x for x in missing_alerts_list if not any(re.search(r, x['name']) for r in ignore)])
    format_string = "{:<30}{}"
    print((format_string.format("Instance ID", "Instance Name")))
    for instance_wo_alerts in filtered_missing_alerts_list:
        print((format_string.format(instance_wo_alerts["ID"], instance_wo_alerts["name"])))
        flag = 1

    # Initializing object of classes
    appcheck = AppAlerts(new_relic_api_key)
    new_relic_obj = NewRelic(new_relic_api_key)
    # Get list of all applications from new relic
    apps_list = appcheck.new_relic_app_extractor()
    # Get list of all applications without alerts
    missing_alerts_list_app = appcheck.missing_alerts_checker(apps_list, alert_policies)
    filtered_missing_alerts_list_app = list([x for x in missing_alerts_list_app if not any(re.search(r, x['name']) for r in ignore)])
    format_string = "{:<20}{}"
    print("")
    print((format_string.format("Application ID", "Application Name")))
    for instance_wo_alerts in filtered_missing_alerts_list_app:
        print((format_string.format(instance_wo_alerts["id"], instance_wo_alerts["name"])))
        flag = 1

    # Initializing object of classes
    browsercheck = BrowserAlerts(new_relic_api_key)
    new_relic_obj = NewRelic(new_relic_api_key)
    # Get list of all browser applications from new relic
    browser_list = browsercheck.new_relic_browser_extractor()
    # Get list of all browser applications without alerts
    missing_alerts_list_browser = browsercheck.missing_alerts_checker(browser_list, alert_policies)
    filtered_missing_alerts_list_browser = list([x for x in missing_alerts_list_browser if not any(re.search(r, x['name']) for r in ignore)])
    format_string = "{:<20}{}"
    print("")
    print((format_string.format("Browser ID", "Browser Name")))
    for instance_wo_alerts in filtered_missing_alerts_list_browser:
        print((format_string.format(instance_wo_alerts["id"], instance_wo_alerts["name"])))
        flag = 1
    sys.exit(flag)


if __name__ == '__main__':
    controller()

