import argparse
import logging as log
import yaml
from datetime import datetime
from git import *
from pprint import pformat
from pprint import pprint
from pymongo import MongoClient, DESCENDING


def release_hashes(repo):
    for ref in repo.remotes.origin.refs:
        if ref.name.startswith('origin/rc/'):
            yield ref.commit.hexsha

def check_all(args):
    config = yaml.safe_load(open(args.config))
    client = MongoClient(uri_from(config['DOC_STORE_CONFIG']))
    repos = [Repo(repo_dir) for repo_dir in config['repos']]
    configuration_repo = Repo(config['configuration_repo'])
    configuration_secure = Repo(config['configuration_secure'])

    for repo in repos:
        for git_hash in release_hashes(repo):
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Monitor git repos for new rc branches.")
    parser.add_argument('-c','--config', required=True,
        help="Config file.")

    args = parser.parse_args()
    check_all(args)
