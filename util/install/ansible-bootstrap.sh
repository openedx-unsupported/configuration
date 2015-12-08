#!/usr/bin/env bash

#
# Script for installing Ansible and the edX configuration repostory
# onto a host to enable running ansible to complete configuration.
# This script can be used by Docker, Packer or any other system
# for building images that requires having ansible available.
#

set -xe

if [[ -z "$ANSIBLE_REPO" ]]; then
  ANSIBLE_REPO="https://github.com/edx/ansible.git"
fi

if [[ -z "$ANSIBLE_VERSION" ]]; then
  ANSIBLE_VERSION="master"
fi

if [[ -z "$CONFIGURATION_REPO" ]]; then
  CONFIGURATION_REPO="https://github.com/edx/configuration.git"
fi

if [[ -z "$CONFIGURATION_VERSION" ]]; then
  CONFIGURATION_VERSION="e0d/hacking"
fi


VIRTUAL_ENV="/tmp/bootstrap"
PYTHON_BIN="${VIRTUAL_ENV}/bin"
ANSIBLE_DIR="/tmp/ansible"
CONFIGURATION_DIR="/tmp/configuration"

cat << EOF
******************************************************************************

Running the edx-ansible bootstrap script with the following arguments:

ANSIBLE_REPO="${ANSIBLE_REPO}"
ANSIBLE_VERSION="${ANSIBLE_VERSION}"
CONFIGURATION_REPO="${CONFIGURATION_REPO}"
CONFIGURATION_VERSION="${CONFIGURATION_VERSION}"

******************************************************************************
EOF


if [[ $(id -u) -ne 0 ]] ; then
    "Please run as root";
    exit 1;
fi

apt-get update -y
apt-get upgrade -y

apt-get install -y software-properties-common python-software-properties git

# Install python 2.7.10
add-apt-repository ppa:fkrull/deadsnakes-python2.7
apt-get update -y
apt-get install -y sudo python2.7 python2.7-dev python-pip python-apt python-yaml python-jinja2 libmysqlclient-dev

pip install virtualenv==13.1.2

# create a new virtual env
/usr/local/bin/virtualenv ${VIRTUAL_ENV}

# ansible bootstrap
git clone --recursive ${ANSIBLE_REPO} ${ANSIBLE_DIR}
cd /tmp/ansible
PATH=$PATH:/tmp/ansible/bin

# Install the configuration repository to install 
# edx-ansible role
git clone ${CONFIGURATION_REPO} ${CONFIGURATION_DIR}
cd ${CONFIGURATION_DIR}
git checkout ${CONFIGURATION_VERSION}
make requirements

cd /tmp/configuration/playbooks/edx-east
${PYTHON_BIN}/ansible-playbook edx_ansible.yml -i '127.0.0.1,' -c local -e "configuration_version=${CONFIGURATION_VERSION}"

# cleanup
rm -rf ${ANSIBLE_DIR}
rm -rf ${CONFIGURATION_DIR}
rm -rf ${VIRTUAL_ENV}

cat << EOF
******************************************************************************

Done bootstrapping, edx-ansible is now installed in /edx/app/edx-ansible.
Time to run some plays.

******************************************************************************
EOF

