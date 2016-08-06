import yaml
import os
import pathlib2
import itertools
import argparse
import logging
import sys

TRAVIS_BUILD_DIR = os.environ.get("TRAVIS_BUILD_DIR")
CONFIG_FILE_PATH = pathlib2.Path(TRAVIS_BUILD_DIR, "util", "parsefiles_config.yml")
LOGGER = logging.getLogger(__name__)

def check_coverage(containers):
    # open config file containing container weights
    config_file_path = pathlib2.Path(CONFIG_FILE_PATH)

    with (config_file_path.open(mode='r')) as file:
        try:
            config = yaml.load(file)
        except yaml.YAMLError, exc:
            LOGGER.error("error in configuration file: %s" % str(exc))
            sys.exit(1)

    # get container weights
    weights = config.get("weights")

    # convert all containers in config file to a list of tuples (<container>, <weight>)
    weights_list = [x.items() for x in weights]
    weights_list = list(itertools.chain.from_iterable(weights_list))

    # performs intersection between weighted containers and input containers
    used_containers = [x for x in weights_list if x[0] in containers]

    # determine which Dockerfiles are not covered; i.e. the set difference of the Dockerfiles to build minus the Dockerfile
    # available to be built is non-empty
    uncovered = set(containers) - set([x[0] for x in used_containers])

    # exit with error code if uncovered Dockerfiles exist
    if uncovered:
        LOGGER.error("The following Dockerfiles are not described in the parsefiles_config.yml file: {}. Please see the following documentation on how to add Dockerfile ranks to the configuration file: {}".format(uncovered, "https://github.com/edx/configuration/blob/master/util/README.md"))
        sys.exit(1)

def arg_parse():

    parser = argparse.ArgumentParser(description = 'Given a list of containers as input and a number of shards, '
        'finds an approximation of the optimal distribution of the containers over the shards, provided a set of hard-coded weights '
        'in parsefiles_config.yml.')
    parser.add_argument('containers', help = "the Dockerfiles that need to be built as the result of some commit change and whose coverage is checked")

    return parser.parse_args()

if __name__ == '__main__':

    args = arg_parse()

    # configure logging
    logging.basicConfig()

    containers = []

    for word in args.containers.split():
        containers.append(word)

    check_coverage(containers)
