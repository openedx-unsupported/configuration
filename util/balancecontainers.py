import argparse
import logging
import os
import sys

try:
    # This script is used by docker.mk at parse-time, which means when you run
    # "make requirements" to install the required Python packages, this script
    # runs before its requirements are installed. That means this import will
    # fail.  To prevent a successful installation from having irrelevant error
    # messages, we catch the failure and exit silently.
    import pathlib2
except ImportError:
    sys.exit(1)

import docker_images


TRAVIS_BUILD_DIR = os.environ.get("TRAVIS_BUILD_DIR", "")
CONFIG_FILE_PATH = pathlib2.Path(TRAVIS_BUILD_DIR, "util", "parsefiles_config.yml")
LOGGER = logging.getLogger(__name__)

def pack_shards(used_images, num_shards):
    """
    Determines an approximation of the optimal way to pack the images into a given number of shards so as to
    equalize the execution time amongst the shards.

    Input:
    used_images: A set of Docker images and their ranks
    num_shards: A number of shards amongst which to distribute the Docker images
    """

    # sorts used containers in descending order on the weight
    sorted_images = sorted(used_images, key = lambda x: x[1], reverse=True)

    shards = []

    # for the number of shards
    for i in range(0, num_shards):
        # initialize initial dict
        shards.append({"images": [], "sum": 0})

    # for each container
    for image in sorted_images:
        # find the shard with the current minimum execution time
        shard = min(shards, key = lambda x: x["sum"])

        # add the current container to the shard
        shard["images"].append(image)

        # add the current container's weight to the shard's total expected execution time
        shard["sum"] += image[1]

    return shards

def read_input():
    """
    Reads input from standard input.
    """

    images = []

    # get images from standard in
    for line in sys.stdin:
        line = line.strip()
        line = line.strip("[]")

        items = line.split()
        images.extend(items)

    return images

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

    # get input from standard in
    images = read_input()

    # get images that are used and described in configuration file
    used_images = docker_images.get_used_images(images)

    # find optimal packing of the images amongst shards
    shards = pack_shards(used_images, args.num_shards)

    # print space separated list of containers for each shard
    for shard in shards:
        middle = " "

        conts = [x[0] for x in shard["images"]]

        line = middle.join(conts)
        print line
