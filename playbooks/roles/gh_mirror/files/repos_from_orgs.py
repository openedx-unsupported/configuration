#!/usr/bin/python
# Generates /var/tmp/repos.txt from
# a yaml file containing a list of
# github organizations

import yaml
import sys
import requests
from os.path import dirname, abspath, join

path = dirname(abspath(__file__))

try:
    with open(join(path, 'orgs.yml')) as f:
        orgs = yaml.load(f)
except IOError:
    print "Unable to read {}/orgs.yml, does it exist?".format(path)
    sys.exit(1)

repos = []

for org in orgs:
    r = requests.get('https://api.github.com/orgs/{}/repos'.format(org))
    org_data = r.json
    for repo_data in org_data:
        repos.append(repo_data['html_url'])

with open('/var/tmp/repos.txt', 'wb') as f:
    f.write('\n'.join(repos))
