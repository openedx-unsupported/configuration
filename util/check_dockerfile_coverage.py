import yaml
import os
import pathlib2
import itertools
import argparse
import logging
import sys
import docker_images

TRAVIS_BUILD_DIR = os.environ.get("TRAVIS_BUILD_DIR", ".")
CONFIG_FILE_PATH = pathlib2.Path(TRAVIS_BUILD_DIR, "util", "parsefiles_config.yml")
LOGGER = logging.getLogger(__name__)

def check_coverage(images, used_images):
    """
    Checks whether all images are described in parsefiles_config.yml and raises an error otherwise, directing toward documentation to resolving the error.

    Input:
    images: the set of images scheduled to be built
    used_images: the subset of images with their ranks that are in the parsefiles_config.yml file
    """

    # determine which Dockerfiles are not covered; i.e. the set difference of the Dockerfiles to build minus the Dockerfile
    # available to be built is non-empty
    uncovered = set(images) - set([x[0] for x in used_images])

    # exit with error code if uncovered Dockerfiles exist
    if uncovered:
        LOGGER.error("The following Dockerfiles are not described in the parsefiles_config.yml file: {}. Please see the following documentation on how to add Dockerfile ranks to the configuration file: {}".format(uncovered, "https://github.com/edx/configuration/blob/master/util/README.md"))
        sys.exit(1)

def arg_parse():

    parser = argparse.ArgumentParser(description = 'Given a list of images as input checks that each input image is described correctly in parsefiles_config.yml')
    parser.add_argument('images', help = "the Dockerfiles that need to be built as the result of some commit change and whose coverage is checked")
    return parser.parse_args()

if __name__ == '__main__':

    args = arg_parse()

    # configure logging
    logging.basicConfig()

    # read input
    images = []

    for i in args.images.split():
        images.append(i)

    # get images that are used and described in configuration file
    used_images = docker_images.get_used_images(images)

    check_coverage(images, used_images)
