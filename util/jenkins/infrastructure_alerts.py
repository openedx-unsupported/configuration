import boto3
import requests
import click


class InfraAlerts:
    def __init__(self, new_relic_api_key):
        self.url_alert_extractor = "https://api.newrelic.com/v2/alerts_policies.json"
        self.headers = {'X-Api-Key': new_relic_api_key}

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
        for region in client_region.describe_regions()['Regions']:
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

    def new_relic_extractor(self):
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
        response.raise_for_status()
        try:
            alert_policies = response.json()
        except ValueError:
            raise Exception("Failed to parse response json. Got:\n{}".format(response.text))
        return alert_policies

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


@click.command()
@click.option('--new-relic-api-key', required=True, help='API Key to use to speak with NewRelic.')
def controller(new_relic_api_key):
    """
    Control execution of all other functions
    Arguments:
        new_relic_api_key (str):
            Get this from cli args
    """
    infracheck = InfraAlerts(new_relic_api_key)
    instance_list = infracheck.edc_extractor()
    alert_policies = infracheck.new_relic_extractor()
    missing_alerts_list = infracheck.missing_alerts_checker(instance_list, alert_policies)


if __name__ == '__main__':
    controller()

