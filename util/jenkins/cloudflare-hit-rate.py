import requests
import argparse

CLOUDFLARE_API_ENDPOINT = "https://api.cloudflare.com/client/v4/"


def calcualte_cache_hit_rate(zone_id, auth_key, email):
    HEADERS = {"Accept": "application/json",
               "X-Auth-Key": auth_key,
               "X-Auth-Email": email}
    res = requests.get(CLOUDFLARE_API_ENDPOINT + "zones/" + zone_id
                       + "/analytics/dashboard?since=-419&continuous=true",
                       headers=HEADERS)
    data = res.json()
    all_req = float(data["result"]["timeseries"][0]["requests"]["all"])
    cached_req = float(data["result"]["timeseries"][0]["requests"]["cached"])
    threshold_limit = cached_req * 100.0 / all_req

    # Add threshold for alerts/alarms

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-z', '--zone', required=True,
                        help="Cloudflare's Zone ID")
    parser.add_argument('-k', '--auth_key', required=True,
                        help="Authentication Key")
    parser.add_argument('-e', '--email', required=True,
                        help="email to use for authentication for CloudFlare API")
    args = parser.parse_args()

    calcualte_cache_hit_rate(args.zone, args.auth_key, args.email)
