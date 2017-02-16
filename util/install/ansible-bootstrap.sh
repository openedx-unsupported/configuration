#!/usr/bin/env bash

#
# Script for installing Ansible and the edX configuration repostory
# onto a host to enable running ansible to complete configuration.
# This script can be used by Docker, Packer or any other system
# for building images that requires having ansible available.
#
# Can be run as follows:
#
# UPGRADE_OS=true CONFIGURATION_VERSION="master" \
# bash <(curl -s https://raw.githubusercontent.com/edx/configuration/master/util/install/ansible-bootstrap.sh)

set -xe

if [[ -z "${ANSIBLE_REPO}" ]]; then
  ANSIBLE_REPO="https://github.com/edx/ansible.git"
fi

if [[ -z "${ANSIBLE_VERSION}" ]]; then
  ANSIBLE_VERSION="master"
fi

if [[ -z "${CONFIGURATION_REPO}" ]]; then
  CONFIGURATION_REPO="https://github.com/edx/configuration.git"
fi

if [[ -z "${CONFIGURATION_VERSION}" ]]; then
  CONFIGURATION_VERSION="master"
fi

if [[ -z "${UPGRADE_OS}" ]]; then
  UPGRADE_OS=false
fi

#
# Bootstrapping constants
#
VIRTUAL_ENV_VERSION="13.1.2"
PIP_VERSION="7.1.2"
SETUPTOOLS_VERSION="18.3.2"
VIRTUAL_ENV="/tmp/bootstrap"
PYTHON_BIN="${VIRTUAL_ENV}/bin"
ANSIBLE_DIR="/tmp/ansible"
CONFIGURATION_DIR="/tmp/configuration"
EDX_PPA="deb http://ppa.edx.org precise main"
EDX_PPA_KEY_SERVER="pgp.mit.edu"
EDX_PPA_KEY_ID="69464050"

cat << EOF
******************************************************************************

Running the edx_ansible bootstrap script with the following arguments:

ANSIBLE_REPO="${ANSIBLE_REPO}"
ANSIBLE_VERSION="${ANSIBLE_VERSION}"
CONFIGURATION_REPO="${CONFIGURATION_REPO}"
CONFIGURATION_VERSION="${CONFIGURATION_VERSION}"

******************************************************************************
EOF


if [[ $(id -u) -ne 0 ]] ;then
    echo "Please run as root";
    exit 1;
fi

if grep -q 'Precise Pangolin' /etc/os-release
then
    SHORT_DIST="precise"
elif grep -q 'Trusty Tahr' /etc/os-release
then
    SHORT_DIST="trusty"
else    
    cat << EOF
    
    This script is only known to work on Ubuntu Precise and Trusty,
    exiting.  If you are interested in helping make installation possible
    on other platforms, let us know.

EOF
   exit 1;
fi

EDX_PPA="deb http://ppa.edx.org ${SHORT_DIST} main"

# Upgrade the OS
apt-get update -y
apt-key update -y

if [ "${UPGRADE_OS}" = true ]; then
    echo "Upgrading the OS..."
    apt-get upgrade -y
fi

# Required for add-apt-repository
apt-get install -y software-properties-common python-software-properties

# Add git PPA
add-apt-repository -y ppa:git-core/ppa

# Add python PPA
apt-key adv --keyserver "${EDX_PPA_KEY_SERVER}" --recv-keys "${EDX_PPA_KEY_ID}"
add-apt-repository -y "${EDX_PPA}"

# Install python 2.7 latest, git and other common requirements
# NOTE: This will install the latest version of python 2.7 and
# which may differ from what is pinned in virtualenvironments
apt-get update -y
apt-get install -y build-essential sudo git-core python2.7 python2.7-dev python-pip python-apt python-yaml python-jinja2 libmysqlclient-dev

pip install --upgrade pip=="${PIP_VERSION}"

# pip moves to /usr/local/bin when upgraded
PATH=/usr/local/bin:${PATH}
pip install setuptools=="${SETUPTOOLS_VERSION}"
pip install virtualenv=="${VIRTUAL_ENV_VERSION}"

# create a new virtual env
/usr/local/bin/virtualenv "${VIRTUAL_ENV}"

PATH="${PYTHON_BIN}":${PATH}

# Install the configuration repository to install 
# edx_ansible role
git clone ${CONFIGURATION_REPO} ${CONFIGURATION_DIR}
cd ${CONFIGURATION_DIR}
git checkout ${CONFIGURATION_VERSION}
make requirements

cd "${CONFIGURATION_DIR}"/playbooks/edx-east
"${PYTHON_BIN}"/ansible-playbook edx_ansible.yml -i '127.0.0.1,' -c local -e "configuration_version=${CONFIGURATION_VERSION}"

# cleanup
rm -rf "${ANSIBLE_DIR}"
rm -rf "${CONFIGURATION_DIR}"
rm -rf "${VIRTUAL_ENV}"

cat << EOF
******************************************************************************

Done bootstrapping, edx_ansible is now installed in /edx/app/edx_ansible.
Time to run some plays.  Activate the virtual env with 

> . /edx/app/edx_ansible/venvs/edx_ansible/bin/activate 

******************************************************************************
EOF

