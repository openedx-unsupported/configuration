#!/usr/bin/python3

# This script is used by the monioring/check-seslimits Jenkins job

from __future__ import absolute_import
from __future__ import print_function
import boto3
import argparse
import sys


# Copied from https://stackoverflow.com/a/41153081
class ExtendAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest) or []
        items.extend(values)
        setattr(namespace, self.dest, items)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--critical', required=True, type=float,
                        help="Critical threshold in percentage")
    parser.add_argument('-w', '--warning', required=False, type=float,
                        help="Warning threshold in percentage (Optional)")
    parser.add_argument('-r', '--region', dest='regions', nargs='+',
                        action=ExtendAction, required=True,
                        help="AWS regions to check")
    args = parser.parse_args()

    if args.warning and args.warning >= args.critical:
        warn_str = "Warning threshold ({})".format(args.warning)
        crit_str = "Critical threshold ({})".format(args.critical)
        print(("ERROR: {} >= {}".format(warn_str, crit_str)))
        sys.exit(1)

    exit_code = 0

    session = boto3.session.Session()
    for region in args.regions:
        ses = session.client('ses', region_name=region)
        data = ses.get_send_quota()
        limit = data["Max24HourSend"]
        current = data["SentLast24Hours"]
        percent = current/limit
        level = None

        if percent >= args.critical:
            level = "CRITICAL"
        elif args.warning and percent >= args.warning:
            level = "WARNING"

        if level:
            print(("{} {}/{} ({}%) - {}".format(region, current, limit, percent,
                  level)))
            exit_code += 1

    sys.exit(exit_code)
