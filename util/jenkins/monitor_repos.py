import argparse
import json
import logging as log
import pickle
import requests
import yaml
from datetime import datetime
from git import Repo
from os import path
from pprint import pformat
from pymongo import MongoClient, DESCENDING
from stage_release import uri_from

def releases(repo):
    """
    Yield a list of all release candidates from the origin.
    """
    for ref in repo.refs:
        if ref.name.startswith('origin/rc/'):
            yield ref

def candidates_since(repo, time):
    """
    Given a repo yield a list of release candidate refs that have a
    commit on them after the passed in time
    """
    for rc in releases(repo):
        last_update = datetime.utcfromtimestamp(rc.commit.committed_date)
        if last_update > time:
            # New or updated RC
            yield rc

def stage_release(url, token, repo, rc):
    """
    Submit a job to stage a new release for the new rc of the repo.
    """
    # Setup the Jenkins params.
    params = []
    params.append({'name': "{}_REF".format(repo), 'value': True})
    params.append({'name': repo, 'value': rc.commit.hexsha})
    build_params = {'parameter': params}
    log.info("New rc found{}, staging new release.".format(rc.name))
    r = requests.post(url,
                      data={"token", token},
                      params={"json": json.dumps(build_params)})
    if r.status_code != 201:
        msg = "Failed to submit request with params: {}"
        raise Exception(msg.format(pformat(build_params)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Monitor git repos for new rc branches.")
    parser.add_argument('-c', '--config', required=True,
        help="Config file.")
    parser.add_argument('-p', '--pickle', default="data.pickle",
        help="Pickle of presistent data.")

    args = parser.parse_args()

    config = yaml.safe_load(open(args.config))

    if path.exists(args.pickle):
        data = pickle.load(open(args.pickle))
    else:
        data = {}

    # Presist the last time we made this check.
    if 'last_check' not in data:
        last_check = datetime.utcnow()
    else:
        last_check = data['last_check']

    data['last_check'] = datetime.utcnow()

    # Find plays that are affected by this repo.
    repos_with_changes = {}
    for repo in config['repos']:
        # Check for new rc candidates.
        for rc in candidates_since(Repo(repo), last_check):
            # Notify stage-release to build for the new repo.
            stage_release(config['abbey_url'], config['abbey_token'], repo, rc)

    pickle.dump(data, open(args.pickle, 'w'))
