#!/usr/bin/python
# Generates /var/tmp/repos.json from
# a yaml file containing a list of
# github organizations

import yaml
import sys
import requests
import json
import subprocess
import os
import logging
from os.path import dirname, abspath, join
from argparse import ArgumentParser


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
            orgs = yaml.load(f)
    except IOError:
        print "Unable to read {}/orgs.yml, does it exist?".format(path)
        sys.exit(1)

    repos = []

    for org in orgs:
        r = requests.get('https://api.github.com/users/{}/repos'.format(org))
        org_data = r.json()
        for repo_data in org_data:
            if 'html_url' in repo_data:
                repos.append({'html_url': repo_data['html_url'],
                              'name': repo_data['name'],
                              'org': repo_data['owner']['login']})

    with open('/var/tmp/repos.json', 'wb') as f:
        f.write(json.dumps(repos))


def update_repos():
    with open('/var/tmp/repos.json') as f:
        repos = json.load(f)
    for repo in repos:
        repo_path = os.path.join(args.datadir, repo['org'], repo['name'])
        if not os.path.exists(repo_path):
            run_cmd('mkdir -p {}'.format(repo_path))
            run_cmd('git clone --mirror {} {}'.format(repo['html_url'], repo_path))
            run_cmd('cd {} && git update-server-info'.format(repo_path))
        else:
            run_cmd('cd {} && git remote-update'.format(repo_path))
            run_cmd('cd {} && git update-server-info'.format(repo_path))

if __name__ == '__main__':
    logging.basicConfig(filename='/var/log/repos-from-orgs.log',
                        level=logging.DEBUG)
    args = parse_args()
    if args.refresh:
        refresh_cache()
    else:
        if not args.datadir:
            print "Please specificy a repository directory"
            sys.exit(1)
        if not os.path.exists('/var/tmp/repos.json'):
            refresh_cache()
        update_repos()
