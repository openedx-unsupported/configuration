#!/usr/bin/env bash

#
# Script for installing Ansible and the edX configuration repository
# onto a host to enable running ansible to complete configuration.
# This script can be used by Docker, Packer or any other system
# for building images that require having ansible available.
#
# Can be run as follows:
#
# UPGRADE_OS=true CONFIGURATION_VERSION="master" \
# bash <(curl -s https://raw.githubusercontent.com/edx/configuration/master/util/install/ansible-bootstrap.sh)

set -xe

if [[ -z "${CONFIGURATION_REPO}" ]]; then
  CONFIGURATION_REPO="https://github.com/edx/configuration.git"
fi

if [[ -z "${CONFIGURATION_VERSION}" ]]; then
    CONFIGURATION_VERSION=${OPENEDX_RELEASE-master}
fi

if [[ -z "${UPGRADE_OS}" ]]; then
  UPGRADE_OS=false
fi

if [[ -z "${RUN_ANSIBLE}" ]]; then
  RUN_ANSIBLE=true
fi

#
# Bootstrapping constants
#
VIRTUAL_ENV_VERSION="16.7.10"
PIP_VERSION="20.0.2"
SETUPTOOLS_VERSION="44.1.0"
VIRTUAL_ENV="/tmp/bootstrap"
PYTHON_BIN="${VIRTUAL_ENV}/bin"
PYTHON_VERSION="3.5"
ANSIBLE_DIR="/tmp/ansible"
CONFIGURATION_DIR="/tmp/configuration"
EDX_PPA_KEY_SERVER="keyserver.ubuntu.com"
EDX_PPA_KEY_ID="B41E5E3969464050"

cat << EOF
******************************************************************************

Running the edx_ansible bootstrap script with the following arguments:

CONFIGURATION_REPO="${CONFIGURATION_REPO}"
CONFIGURATION_VERSION="${CONFIGURATION_VERSION}"

******************************************************************************
EOF


if [[ $(id -u) -ne 0 ]] ;then
    echo "Please run as root";
    exit 1;
fi

if grep -q 'Trusty Tahr' /etc/os-release
then
    SHORT_DIST="trusty"
elif grep -q 'Xenial Xerus' /etc/os-release
then
    SHORT_DIST="xenial"
elif grep -q 'Bionic Beaver' /etc/os-release
then
    SHORT_DIST="bionic"
elif grep -q 'Focal Fossa' /etc/os-release
then
    SHORT_DIST="focal"
else
    cat << EOF

    This script is only known to work on Ubuntu Trusty, Xenial, and Bionic;
    exiting.  If you are interested in helping make installation possible
    on other platforms, let us know.

EOF
   exit 1;
fi

EDX_PPA="deb http://ppa.edx.org ${SHORT_DIST} main"

# Upgrade the OS
rm -r /var/lib/apt/lists/* -vf
apt-get update -y

# To apt-key update in bionic, gnupg is needed.
if [[ "${SHORT_DIST}" == bionic ]] ;then
  apt-get install -y gnupg
fi

apt-key update -y

if [ "${UPGRADE_OS}" = true ]; then
    echo "Upgrading the OS..."
    apt-get upgrade -y
fi

# Required for add-apt-repository
apt-get install -y software-properties-common
if [[ "${SHORT_DIST}" != trusty ]] && [[ "${SHORT_DIST}" != xenial ]] && [[ "${SHORT_DIST}" != bionic ]] && [[ "${SHORT_DIST}" != focal ]] ;then
  apt-get install -y python-software-properties
fi

# Add git PPA
add-apt-repository -y ppa:git-core/ppa

# For older software we need to install our own PPA
# Phased out with Ubuntu 18.04 Bionic and Ubuntu 20.04 Focal
if [[ "${SHORT_DIST}" != bionic ]] && [[ "${SHORT_DIST}" != focal ]] ;then
  apt-key adv --keyserver "${EDX_PPA_KEY_SERVER}" --recv-keys "${EDX_PPA_KEY_ID}"
  add-apt-repository -y "${EDX_PPA}"
fi

# Add deadsnakes repository for python3.5 usage in
# Ubuntu versions different than xenial.
if [[ "${SHORT_DIST}" != xenial ]] ;then
  add-apt-repository -y ppa:deadsnakes/ppa
fi

# Install python 2.7 latest, git and other common requirements
# NOTE: This will install the latest version of python 2.7 and
# which may differ from what is pinned in virtualenvironments
apt-get update -y

if [[ "${SHORT_DIST}" != focal ]] ;then
  apt-get install -y python2.7 python2.7-dev python-pip python-apt python-jinja2 build-essential sudo git-core libmysqlclient-dev libffi-dev libssl-dev
else
  apt-get install -y python3-pip python3-apt python3-jinja2 build-essential sudo git-core libmysqlclient-dev libffi-dev libssl-dev
fi

apt-get install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-dev python3-pip python3-apt

# We want to link pip to pip3 for Ubuntu versions that don't have python 2.7 so older scripts work there
# Applies to Ubuntu 20.04 Focal
if [[ "${SHORT_DIST}" != trusty ]] && [[ "${SHORT_DIST}" != xenial ]] && [[ "${SHORT_DIST}" != bionic ]] && [[ "${SHORT_DIST}" != focal ]] ;then
  sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1
  sudo update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
  ln -s /usr/bin/pip3 /usr/bin/pip
fi

python${PYTHON_VERSION} -m pip install --upgrade pip=="${PIP_VERSION}"

# pip moves to /usr/local/bin when upgraded
PATH=/usr/local/bin:${PATH}
python${PYTHON_VERSION} -m pip install setuptools=="${SETUPTOOLS_VERSION}"
python${PYTHON_VERSION} -m pip install virtualenv=="${VIRTUAL_ENV_VERSION}"

if [[ "true" == "${RUN_ANSIBLE}" ]]; then
    # create a new virtual env
    /usr/local/bin/virtualenv --python=python${PYTHON_VERSION} "${VIRTUAL_ENV}"

    PATH="${PYTHON_BIN}":${PATH}

    # Install the configuration repository to install
    # edx_ansible role
    git clone ${CONFIGURATION_REPO} ${CONFIGURATION_DIR}
    cd ${CONFIGURATION_DIR}
    git checkout ${CONFIGURATION_VERSION}
    make requirements

    cd "${CONFIGURATION_DIR}"/playbooks
    "${PYTHON_BIN}"/ansible-playbook edx_ansible.yml -i '127.0.0.1,' -c local -e "CONFIGURATION_VERSION=${CONFIGURATION_VERSION}"

    # cleanup
    rm -rf "${ANSIBLE_DIR}"
    rm -rf "${CONFIGURATION_DIR}"
    rm -rf "${VIRTUAL_ENV}"
    rm -rf "${HOME}/.ansible"

    cat << EOF
    ******************************************************************************

    Done bootstrapping, edx_ansible is now installed in /edx/app/edx_ansible.
    Time to run some plays.  Activate the virtual env with

    > . /edx/app/edx_ansible/venvs/edx_ansible/bin/activate

    ******************************************************************************
EOF
else
    mkdir -p /edx/ansible/facts.d
    echo '{ "ansible_bootstrap_run": true }' > /edx/ansible/facts.d/ansible_bootstrap.json
fi
