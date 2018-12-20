import requests
import click


class AppAlerts:
    def __init__(self, new_relic_api_key):
        self.url_app_extractor = "https://api.newrelic.com/v2/applications.json"
        self.url_alert_extractor = "https://api.newrelic.com/v2/alerts_policies.json"
        self.headers = {'X-Api-Key': new_relic_api_key}

    def new_relic_app_extractor(self):
        """
        Return:
             Return list all applications in new relic
        """
        response = requests.get(self.url_app_extractor, headers=self.headers)
        response.raise_for_status()
        try:
            apps_list = response.json()
        except ValueError:
            raise Exception("Failed to parse response json. Got:\n{}".format(response.text))
        return apps_list["applications"]

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
        response.raise_for_status()
        try:
            alert_policies = response.json()
        except ValueError:
            raise Exception("Failed to parse response json. Got:\n{}".format(response.text))
        return alert_policies

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


@click.command()
@click.option('--new-relic-api-key', required=True, help='API Key to use to speak with NewRelic.')
def controller(new_relic_api_key):
    """
    Control execution of all other functions
    Arguments:
        new_relic_api_key (str):
            Get this from cli args
    """
    appcheck = AppAlerts(new_relic_api_key)
    apps_list = appcheck.new_relic_app_extractor()
    alert_policies = appcheck.new_relic_policies_extractor()
    missing_alerts_list = appcheck.missing_alerts_checker(apps_list, alert_policies)


if __name__ == '__main__':
    controller()

