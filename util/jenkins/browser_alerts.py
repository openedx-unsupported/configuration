import requests
import click


class BrowserAlerts:
    def __init__(self, new_relic_api_key):
        self.url_browser_extractor = "https://api.newrelic.com/v2/browser_applications.json"
        self.url_alert_extractor = "https://api.newrelic.com/v2/alerts_policies.json"
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
        response.raise_for_status()
        try:
            browser_list = response.json()
        except ValueError:
            raise Exception("Failed to parse response json. Got:\n{}".format(response.text))
        return browser_list["browser_applications"]

    def new_relic_policies_extractor(self, app_list):
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
def controller(new_relic_api_key):
    """
    Control execution of all other functions
    Arguments:
        new_relic_api_key (str):
            Get this from cli args
    """
    browsercheck = BrowserAlerts(new_relic_api_key)
    browser_list = browsercheck.new_relic_browser_extractor()
    alert_policies = browsercheck.new_relic_policies_extractor(browser_list)
    missing_alerts_list = browsercheck.missing_alerts_checker(browser_list, alert_policies)


if __name__ == '__main__':
    controller()

