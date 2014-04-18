#!/bin/sh
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
if [[ ! "$(lsb_release -d | cut -f2)" =~ $'Ubuntu 12.04' ]]; then
   echo "This script is only known to work on Ubuntu 12.04, exiting...";
   exit;
fi

##
## Install system pre-requisites
##
sudo apt-get install -y build-essential software-properties-common python-software-properties curl git-core libxml2-dev libxslt1-dev python-pip python-apt python-dev
wget https://bitbucket.org/pypa/setuptools/raw/0.8/ez_setup.py -O - | sudo python
sudo pip install --upgrade pip
sudo pip install --upgrade virtualenv

##
## Clone the configuration repository and run Ansible
##
cd /var/tmp
git clone -b release https://github.com/edx/configuration

##
## Install the ansible requirements
##
cd /var/tmp/configuration
sudo pip install -r requirements.txt

##
## Run the edx_sandbox.yml playbook in the configuration/playbooks directory
##
cd /var/tmp/configuration/playbooks && sudo ansible-playbook -c local ./edx_sandbox.yml -i "localhost,"
