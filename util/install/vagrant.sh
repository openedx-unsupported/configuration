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
   echo "This script is only know to work on Ubuntu 12.04, exiting...";
   exit;
fi

##
## Install system pre-requisites
##
sudo apt-get install -y python-pip python-apt git-core build-essential python-dev libxml2-dev libxslt-dev curl
sudo apt-get install -y software-properties-common python-software-properties
sudo apt-get install -y python-pip python-dev build-essential

sudo pip install --upgrade pip
sudo pip install --upgrade virtualenv

##
## Clone the configuration repository and run Ansible
##
cd /var/tmp
git clone https://github.com/edx/configuration

##
## Install the ansible requirements
##
cd /var/tmp/configuration
sudo pip install -r requirements.txt

##
## Run the edx_sandbox.yml playbook in the configuration/playbooks directory
##
cd /var/tmp/configuration/playbooks
sudo ansible-playbook -c local ./edx_sandbox.yml -i "localhost,"
