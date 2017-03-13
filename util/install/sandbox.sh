#!/bin/bash
##
## Installs the pre-requisites for running edX on a single Ubuntu 12.04
## instance.  This script is provided as a convenience and any of these
## steps could be executed manually.
##
## Note that this script requires that you have the ability to run
## commands as root via sudo.  Caveat Emptor!
##

##
## Sanity check
##
if [[ `lsb_release -rs` != "16.04" ]]; then
   echo "This script is only known to work on Ubuntu 16.04, exiting...";
   exit;
fi

##
## Set ppa repository source for gcc/g++ 4.8 in order to install insights properly
##
sudo apt-get install -y python-software-properties
sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test

##
## Update and Upgrade apt packages
##
sudo apt-get update -y
sudo apt-get upgrade -y

##
## Install system pre-requisites
##
sudo apt-get install -y build-essential software-properties-common curl git-core libxml2-dev libxslt1-dev python-pip libmysqlclient-dev python-apt python-dev libxmlsec1-dev libfreetype6-dev swig gcc g++
sudo pip install --upgrade pip==8.1.2
sudo pip install --upgrade setuptools==24.0.3
sudo -H pip install --upgrade virtualenv==15.0.2

##
## Overridable version variables in the playbooks. Each can be overridden
## individually, or with $OPENEDX_RELEASE.
##
VERSION_VARS=(
  edx_platform_version
  certs_version
  forum_version
  xqueue_version
  configuration_version
  demo_version
  NOTIFIER_VERSION
  INSIGHTS_VERSION
  ANALYTICS_API_VERSION
  ECOMMERCE_VERSION
  ECOMMERCE_WORKER_VERSION
  PROGRAMS_VERSION
)

EXTRA_VARS="-e SANDBOX_ENABLE_ECOMMERCE=True $EXTRA_VARS"
for var in ${VERSION_VARS[@]}; do
  # Each variable can be overridden by a similarly-named environment variable,
  # or OPENEDX_RELEASE, if provided.
  ENV_VAR=$(echo $var | tr '[:lower:]' '[:upper:]')
  eval override=\${$ENV_VAR-\$OPENEDX_RELEASE}
  if [ -n "$override" ]; then
    EXTRA_VARS="-e $var=$override $EXTRA_VARS"
  fi
done

# my-passwords.yml is the file made by generate-passwords.sh.
if [[ -f my-passwords.yml ]]; then
    EXTRA_VARS="-e@$(pwd)/my-passwords.yml $EXTRA_VARS"
fi

CONFIGURATION_VERSION=${CONFIGURATION_VERSION-${OPENEDX_RELEASE-master}}

##
## Clone the configuration repository and run Ansible
##
cd /var/tmp
git clone https://github.com/edx/configuration
cd configuration
git checkout $CONFIGURATION_VERSION
git pull

##
## Install the ansible requirements
##
cd /var/tmp/configuration
sudo -H pip install -r requirements.txt

##
## Run the edx_sandbox.yml playbook in the configuration/playbooks directory
##
cd /var/tmp/configuration/playbooks && sudo -E ansible-playbook -c local ./edx_sandbox.yml -i "localhost," $EXTRA_VARS
