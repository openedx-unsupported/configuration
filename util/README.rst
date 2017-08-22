How to add Dockerfiles to configuration file
############################################

The script that handles distributing build jobs across Travis CI shards relies
on the parsefiles\_config YAML file. This file contains a mapping from each
application that has a Dockerfile to its corresponding weight/rank. The rank
refers to the approximate running time of a Travis Docker build for that
application's Dockerfile. When adding a new Dockerfile to the configuration
repository, this configuration file needs to be manually updated in order to
ensure that the Dockerfile is also built.

To modify configuration file:

1.  Edit the docker.mk file:
2.  Modify docker\_test to include date commands.

    Replace

    ``$(docker_test)%: .build/%/Dockerfile.test     docker build -t $*:test -f $< .``

    with

    ``$(docker_test)%: .build/%/Dockerfile.test     date     docker build -t $*:test -f $< .     date``

3.  Replace the command that runs the dependency analyzer with a line to build
    your Dockerfiles.

    For example, if adding Dockerfile for ecommerce, rabbit mq, replace

    ``images:=$(shell git diff --name-only $(TRAVIS_COMMIT_RANGE) | python util/parsefiles.py)``

    with

    ``images:= ecommerce rabbitmq``

4.  Replace the command that runs the balancing script with a line to build all
    images.

    Replace

    ``docker.test.shard: $(foreach image,$(shell echo $(images) | python util/balancecontainers.py $(SHARDS) | awk 'NR%$(SHARDS)==$(SHARD)'),$(docker_test)$(image))``

    with

    ``docker.test.shard: $(foreach image,$(shell echo $(images) | tr ' ' '\n' | awk 'NR%$(SHARDS)==$(SHARD)'),$(docker_test)$(image))``

5.  Commit and push to your branch.

6.  Wait for Travis CI to run the builds.

7.  Upon completion, examine the Travis CI logs to find where your Dockerfile
    was built (search for "docker build -t"). Your Dockerfile should be built
    by one of the build jobs with "MAKE_TARGET=docker.test.shard". Find the
    amount of time the build took by comparing the output of the date command
    before the build command starts and the date command after the build
    command completes.

8.  Round build time to a whole number, and add it to the
    configuration/util/parsefiles\_config.yml file.

9.  Undo steps 1a, 1b, 1c to revert back to the original state of the docker.mk
    file.

10. Commit and push to your branch. Your Dockerfile should now be built as a
    part of the Travis CI tests.
