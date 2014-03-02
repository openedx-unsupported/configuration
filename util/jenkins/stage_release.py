"""
Take in a YAML file with the basic data of all the things we could
deploy and command line hashes for the repos that we want to deploy
right now.

Example Config YAML file:
---
DOC_STORE_CONFIG:
    hosts: [ list, of, mongo, hosts]
    port: #
    db: 'db'
    user: 'jenkins'
    password: 'password'

configuration_repo: "/path/to/configuration/repo"
configuration_secure_repo: "/path/to/configuration-secure"

repos:
    edxapp:
        plays:
        - edxapp
        - worker
    xqueue:
        plays:
        - xqueue
    6.00x:
        plays:
        - xserver
    xserver:
        plays:
        - xserver

deployments:
    edx:
    - stage
    - prod
    edge:
    - stage
    - prod
    loadtest:
    - stage

# A jenkins URL to post requests for building AMIs
abbey_url: "http://...."

# A mapping of plays to base AMIs
base_ami:{}

# The default AMI to use if there isn't one specific to your plays.
default_base_ami: ''
---
"""
import argparse
import json
import yaml
import logging as log
import requests
from datetime import datetime
from git import Repo
from pprint import pformat
from pymongo import MongoClient, DESCENDING

log.basicConfig(level=log.DEBUG)

def uri_from(doc_store_config):
    """
    Convert the below structure to a mongodb uri.

    DOC_STORE_CONFIG:
      hosts:
        - 'host1.com'
        - 'host2.com'
      port: 10012
      db: 'devops'
      user: 'username'
      password: 'password'
    """

    uri_format = "mongodb://{user}:{password}@{hosts}/{db}"
    host_format = "{host}:{port}"

    port = doc_store_config['port']
    host_uris = [host_format.format(host=host,port=port) for host in doc_store_config['hosts']]
    return uri_format.format(
        user=doc_store_config['user'],
        password=doc_store_config['password'],
        hosts=",".join(host_uris),
        db=doc_store_config['db'])

def prepare_release(args):
    config = yaml.safe_load(open(args.config))
    mongo_uri = uri_from(config['DOC_STORE_CONFIG'])
    client = MongoClient(mongo_uri)
    db = client[config['DOC_STORE_CONFIG']['db']]

    # Get configuration repo versions
    config_repo_ver = Repo(config['configuration_repo']).commit().hexsha
    config_secure_ver = Repo(config['configuration_secure_repo']).commit().hexsha

    # Parse the vars.
    var_array = map(lambda key_value: key_value.split('='), args.REPOS)
    update_repos = { item[0]:item[1] for item in var_array }
    log.info("Update repos: {}".format(pformat(update_repos)))

    release = {}
    now = datetime.utcnow()
    release['_id'] = args.release_id
    release['date_created'] = now
    release['date_modified'] = now
    release['build_status'] = 'Unknown'
    release['build_user'] = args.user


    release_coll = db[args.deployment]
    releases = release_coll.find({'build_status': 'Succeeded'}).sort('_id', DESCENDING)
    all_plays = {}

    try:
        last_successful = releases.next()
        all_plays = last_successful['plays']
    except StopIteration:
        # No successful builds.
        log.warn("No Previously successful builds.")

    # For all repos that were updated
    for repo, ref in update_repos.items():
        var_name = "{}_version".format(repo.replace('-','_'))
        if repo not in config['repos']:
            raise Exception("No info for repo with name '{}'".format(repo))

        # For any play that uses the updated repo
        for play in config['repos'][repo]:
            if play not in all_plays:
                all_plays[play] = {}

            if 'vars' not in all_plays[play]:
                all_plays[play]['vars'] = {}

            all_plays[play]['vars'][var_name] = ref
            # Configuration to use to build these AMIs
            all_plays[play]['configuration_ref'] = config_repo_ver
            all_plays[play]['configuration_secure_ref'] = config_secure_ver

            # Set amis to None for all envs of this deployment
            all_plays[play]['amis'] = {}
            for env in config['deployments'][args.deployment]:
                # Check the AMIs collection to see if an ami already exist
                # for this configuration.
                potential_ami = ami_for(db, env,
                                        args.deployment,
                                        play, config_repo_ver,
                                        config_secure_ver,
                                        ref)
                if potential_ami:
                    all_plays[play]['amis'][env] = potential_ami['_id']
                else:
                    all_plays[play]['amis'][env] = None

    release['plays'] = all_plays
    if args.noop:
        print("Would insert into release collection: {}".format(pformat(release)))
    else:
        release_coll.insert(release)
    # All plays that need new AMIs have been updated.
    notify_abbey(config, args.deployment,
                 all_plays, args.release_id, mongo_uri, config_repo_ver,
                 config_secure_ver, args.noop)

def ami_for(db, env, deployment, play, configuration,
    configuration_secure, ansible_vars):

    ami_signature = {
        'env': env,
        'deployment': deployment,
        'play': play,
        'configuration_ref': configuration,
        'configuration_secure_ref': configuration_secure,
        'vars': ansible_vars,
    }

    return db.amis.find_one(ami_signature)

def notify_abbey(config, deployment, all_plays, release_id,
                 mongo_uri, configuration_ref, configuration_secure_ref, noop=False):
    abbey_url = config['abbey_url']
    base_amis = config['base_amis']
    default_base = config['default_base_ami']

    for play_name, play in all_plays.items():
        for env, ami in play['amis'].items():
            if ami is None:
                params = {}
                params['play'] = play_name
                params['deployment'] = deployment
                params['environment'] = env
                params['refs'] = yaml.safe_dump(play['vars'], default_flow_style=False)
                params['release_id'] = release_id
                params['mongo_uri'] = mongo_uri
                params['configuration'] = configuration_ref
                params['configuration_secure'] = configuration_secure_ref
                params['base_ami'] = base_amis.get(play_name, default_base)

                log.info("Need ami for {}".format(pformat(params)))
                if noop:
                    r = requests.Request('POST', abbey_url, params=params)
                    url = r.prepare().url
                    print("Would have posted: {}".format(url))
                else:
                    r = requests.post(abbey_url, params=params)

                    log.info("Sent request got {}".format(r))
                    if r.status_code != 200:
                        # Something went wrong.
                        msg = "Failed to submit request with params: {}"
                        raise Exception(msg.format(pformat(params)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare a new release.")
    parser.add_argument('-c', '--config', required=True, help="Configuration for deploys")
    parser.add_argument('-u', '--user', required=True, help="User staging the release.")
    msg = "The deployment to build for eg. edx, edge, loadtest"
    parser.add_argument('-d', '--deployment', required=True, help=msg)
    parser.add_argument('-r', '--release-id', required=True, help="Id of Release.")
    parser.add_argument('-n', '--noop', action='store_true',
        help="Run without sending requests to abbey.")
    parser.add_argument('REPOS', nargs='+',
        help="Any number of var=value(no spcae around '='" + \
             " e.g. 'edxapp=3233bac xqueue=92832ab'")

    args = parser.parse_args()
    log.debug(args)
    prepare_release(args)
