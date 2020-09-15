"""
CloudFlare API
https://api.cloudflare.com/#zone-analytics-dashboard

"""
from __future__ import absolute_import
from __future__ import print_function
import requests
import argparse
import sys

CLOUDFLARE_API_ENDPOINT = "https://api.cloudflare.com/client/v4/"


def calcualte_cache_hit_rate(zone_id, auth_key, email, threshold):
    HEADERS = {"Accept": "application/json",
               "X-Auth-Key": auth_key,
               "X-Auth-Email": email}
    # for the past one hour, -59 indicates minutes, we can go
    # beyond that as well, for example for last 15
    # hours it will be -899
    PARAMS = {"since": "-59", "continuous": "true"}
    res = requests.get(CLOUDFLARE_API_ENDPOINT + "zones/" + zone_id
                       + "/analytics/dashboard", headers=HEADERS,
                       params=PARAMS)
    try:
        data = res.json()
        all_req = float(data["result"]["timeseries"][0]["requests"]["all"])
        cached_req = float(data["result"]["timeseries"][0]["requests"]["cached"])
        current_cache_hit_rate = cached_req / all_req * 100
        if current_cache_hit_rate < threshold:
            sys.exit(1)

    except Exception as error:
        print(("JSON Error: {} \n Content returned from API call: {}".format(error, res.text)))




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-z', '--zone', required=True,
                        help="Cloudflare's Zone ID")
    parser.add_argument('-k', '--auth_key', required=True,
                        help="Authentication Key")
    parser.add_argument('-e', '--email', required=True,
                        help="email to use for authentication for CloudFlare API")
    parser.add_argument('-t', '--threshold', required=True,
                        help="Threshold limit to be passed to check against it")
    args = parser.parse_args()

    calcualte_cache_hit_rate(args.zone, args.auth_key, args.email, args.threshold)
