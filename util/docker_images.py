from __future__ import absolute_import
import yaml
import os
import pathlib2
import itertools
import sys

TRAVIS_BUILD_DIR = os.environ.get("TRAVIS_BUILD_DIR", "")
CONFIG_FILE_PATH = pathlib2.Path(TRAVIS_BUILD_DIR, "util", "parsefiles_config.yml")

def get_used_images(images):
    """
    Returns the images and their ranks that are scheduled to be built and that exist in the configuration file.

    Input:
    images: A set of Docker images
    """

    # open config file containing container weights
    config_file_path = pathlib2.Path(CONFIG_FILE_PATH)

    with (config_file_path.open(mode='r')) as file:
        try:
            config = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            LOGGER.error("error in configuration file: %s" % str(exc))
            sys.exit(1)

    # get container weights
    weights = config.get("weights")

    ignore_list = config.get("docker_ignore_list")

    # convert all images in config file to a list of tuples (<image>, <weight>)
    weights_list = [list(x.items()) for x in weights]
    weights_list = list(itertools.chain.from_iterable(weights_list))

    # performs intersection between weighted images and input images
    return [x for x in weights_list if x[0] in images and x[0] not in ignore_list]
