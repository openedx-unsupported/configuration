#!/usr/bin/python
#   Given a list of repos in a yaml
#   file will create or update mirrors
#
#   Generates /var/tmp/repos.json from
#   a yaml file containing a list of
#   github organizations

from __future__ import absolute_import
from __future__ import print_function
import yaml
import sys
import requests
import json
import subprocess
import os
import logging
import fcntl
from os.path import dirname, abspath, join
from argparse import ArgumentParser

def check_running(run_type=''):

    pid_file = '{}-{}.pid'.format(
        os.path.basename(__file__),run_type)
    fp = open(pid_file, 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        # another instance is running
        sys.exit(0)

def run_cmd(cmd):
    logging.debug('running: {}\n'.format(cmd))
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=True)
    for line in iter(process.stdout.readline, ""):
        logging.debug(line)


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-r', '--refresh', action='store_true',
                        help="Refresh the list of repos", default=False)
    parser.add_argument('-d', '--datadir', help="repo directory")
    return parser.parse_args()


def refresh_cache():
    path = dirname(abspath(__file__))
    try:
        with open(join(path, 'orgs.yml')) as f:
            orgs = yaml.safe_load(f)
    except IOError:
        print("Unable to read {}/orgs.yml, does it exist?".format(path))
        sys.exit(1)

    repos = []

    for org in orgs:
        page = 1
        while True:
            r = requests.get('https://api.github.com/users/{}/repos?page={}'.format(org, page))
            org_data = r.json()
            # request pages until we get zero results
            if not isinstance(org_data, list) or len(org_data) == 0:
                break
            for repo_data in org_data:
                if 'html_url' in repo_data:
                    repos.append({'html_url': repo_data['html_url'],
                                  'name': repo_data['name'],
                                  'org': repo_data['owner']['login']})
            page += 1
    with open('/var/tmp/repos.json', 'wb') as f:
        f.write(json.dumps(repos))


def update_repos():
    with open('/var/tmp/repos.json') as f:
        repos = json.load(f)
    for repo in repos:
        repo_path = os.path.join(args.datadir, repo['org'], repo['name'] + '.git')
        if not os.path.exists(repo_path):
            run_cmd('mkdir -p {}'.format(repo_path))
            run_cmd('git clone --mirror {} {}'.format(repo['html_url'], repo_path))
            run_cmd('cd {} && git update-server-info'.format(repo_path))
        else:
            run_cmd('cd {} && git fetch --all --tags'.format(repo_path))
            run_cmd('cd {} && git update-server-info'.format(repo_path))

if __name__ == '__main__':
    args = parse_args()
    logging.basicConfig(filename='/var/log/repos-from-orgs.log',
                        level=logging.DEBUG)
    if args.refresh:
        check_running('refresh')
        refresh_cache()
    else:
        check_running()
        if not args.datadir:
            print("Please specificy a repository directory")
            sys.exit(1)
        if not os.path.exists('/var/tmp/repos.json'):
            refresh_cache()
        update_repos()
