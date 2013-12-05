import argparse
import yaml
from git import *
from pprint import pformat
from pprint import pprint
from pymongo import MongoClient


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

def release_hashes(repo):
    for ref in repo.remotes.origin.refs:
        if ref.name.startswith('origin/rc/'):
            yield ref.commit.hexsha

def check_all(config):
    client = MongoClient(uri_from(config['DOC_STORE_CONFIG']))
    repos = [Repo(repo_dir) for repo_dir in config['repos']]
    configuration_repo = Repo(config['configuration_repo'])
    configuration_secure = Repo(config['configuration_secure'])

    for repo in repos:
        for git_hash in release_hashes(repo):
            pass
             

def have_ami(ami_signature, db):
    db.amis.find_one(ami_signature)
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Monitor git repos for new rc branches.")
    parser.add_argument('-c','--config', required=True,
        help="Config file.")

    subparsers = parser.add_subparsers(help="The running mode of the script.")
   
    msg = "Check all rc branches of all repos specified in config."
    parse_monitor = subparsers.add_parser('all', help=msg)
    parse_monitor.set_defaults(all=True)

    msg = "Manually trigger a build for a given play."
    manual_monitor = subparsers.add_parser('single', help=msg)
    manual_monitor.set_defaults(all=False)
    manual_monitor.add_argument("--env", required=True, 
        help="The environment to build for.")
    manual_monitor.add_argument("--deployment", required=True, 
        help="e.g. edx, edge, etc.")
    manual_monitor.add_argument("--play", required=True, 
        help="The ansible play to run.")
    manual_monitor.add_argument("--cfg-repo",
        help="Hash of the configuration repo to use.")
    manual_monitor.add_argument("--cfg-secure-repo",
        help="Hash of the configuration-secure repo to use.")
    manual_monitor.add_argument("VARS", nargs="+",
        help="Any number of var=value(no spcae around '='" + \
             " e.g. 'edxapp=3233bac xqueue=92832ab'")
    
    args = parser.parse_args()
    config = yaml.safe_load(open(args.config))

    if args.all:
        check_all(config)
    else:
        client = MongoClient(uri_from(config['DOC_STORE_CONFIG']))
        db = client[config['DOC_STORE_CONFIG']['db']]
        # Parse the vars.
        var_array = map(lambda key_value: key_value.split('='), args.VARS)
        ansible_vars = { item[0]:item[1] for item in var_array }
        # Check the specified play.
        if not args.cfg_repo:
            # Look up the config repo if it's not provided.
            repo = Repo(config['configuration_repo'])
            args.cfg_repo = repo.commit().hexsha

        if not args.cfg_secure_repo:
            # Look up the configuration secure repo if it's not provided.
            repo = Repo(config['configuration_secure'])
            args.cfg_secure_repo= repo.commit().hexsha

        ami_signature = {
            'env': args.env,
            'deployment': args.deployment,
            'play': args.play,
            'configuration_ref': args.cfg_repo,
            'configuration_secure_ref': args.cfg_secure_repo,
            'vars': ansible_vars,
        }

        ami_item = db.amis.find_one(ami_signature)
        if not ami_item:
            print("Need ami for:\n{}".format(pformat(ami_signature)))
        else:
            print("Ami exists:\n{}".format(pformat(ami_item)))
