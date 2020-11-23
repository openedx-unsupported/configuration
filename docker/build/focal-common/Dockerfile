ARG BASE_IMAGE_TAG=latest
FROM ubuntu:focal
LABEL maintainer="edxops"

# Set locale to UTF-8 which is not the default for docker.
# See the links for details:
# http://jaredmarkell.com/docker-and-locales/
# https://github.com/docker-library/python/issues/13
# https://github.com/docker-library/python/pull/14/files
# Also install software-properties-common to get apt-add-repository
# Also install iproute2 because ansible needs it for the ansible_default_ipv4.address fact
RUN apt-get update &&\
    apt-get install -y cron iproute2 locales software-properties-common &&\
    locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ENV CONFIGURATION_REPO="https://github.com/edx/configuration.git"
ARG OPENEDX_RELEASE=master
ENV CONFIGURATION_VERSION="${OPENEDX_RELEASE}"

# Add the deadsnakes PPA to install Python 3.8
RUN apt-add-repository -y ppa:deadsnakes/ppa
RUN apt-get update &&\
    apt-get install -y python3.8-dev python3.8-distutils

ADD util/install/ansible-bootstrap.sh /tmp/ansible-bootstrap.sh
RUN chmod +x /tmp/ansible-bootstrap.sh
RUN /tmp/ansible-bootstrap.sh
