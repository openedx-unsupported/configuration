import yaml
import os
import pathlib2
import itertools
import sys
import argparse
import logging

TRAVIS_BUILD_DIR = os.environ.get("TRAVIS_BUILD_DIR")
CONFIG_FILE_PATH = pathlib2.Path(TRAVIS_BUILD_DIR, "util", "parsefiles_config.yml")
LOGGER = logging.getLogger(__name__)

def pack_containers(containers, num_shards):
    """
    Determines an approximation of the optimal way to pack the containers into a given number of shards so as to
    equalize the execution time amongst the shards.

    Input:
    containers: A set of Docker containers
    num_shards: A number of shards amongst which to distribute the Docker containers
    """

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

    # sorts used containers in descending order on the weight
    sorted_containers = sorted(used_containers, key = lambda x: x[1], reverse=True) 

    shards = []

    # for the number of shards
    for i in range(0, num_shards):
        # initialize initial dict
        shards.append({"containers": [], "sum": 0})

    # for each container
    for container in sorted_containers:
        # find the shard with the current minimum execution time
        shard = min(shards, key = lambda x: x["sum"])

        # add the current container to the shard
        shard["containers"].append(container)

        # add the current container's weight to the shard's total expected execution time
        shard["sum"] += container[1]

    return shards

def arg_parse():

    parser = argparse.ArgumentParser(description = 'Given a list of containers as input and a number of shards, '
        'finds an approximation of the optimal distribution of the containers over the shards, provided a set of hard-coded weights '
        'in parsefiles_config.yml.')
    parser.add_argument('num_shards', type = int, help = "the number of shards amongst which to distribute Docker builds")

    return parser.parse_args()

if __name__ == '__main__':

    args = arg_parse()

    # configure logging
    logging.basicConfig()

    containers = []

    # get containers from standard in
    for line in sys.stdin:
        line = line.strip()
        line = line.strip("[]")

        items = line.split()
        containers.extend(items)

    # find optimal packing of the containers amongst shards
    shards = pack_containers(containers, args.num_shards)

    # print space separated list of containers for each shard
    for shard in shards:
        middle = " "

        conts = [x[0] for x in shard["containers"]]

        line = middle.join(conts)
        print line
