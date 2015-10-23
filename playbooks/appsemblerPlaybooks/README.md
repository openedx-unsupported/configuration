#How to use this playbook
Run this playbook from the edxapp server.

- on the edxapp server run:
```
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get install -y build-essential software-properties-common python-software-properties curl git-core libxml2-dev libxslt1-dev libfreetype6-dev python-pip python-apt python-dev libxmlsec1-dev swig
sudo pip install --upgrade pip
sudo pip install --upgrade virtualenv

git clone https://github.com/appsembler/configuration.git
cd configuration
git checkout appsembler/release
sudo pip install -r requirements.txt
cd playbooks/appsemblerPlaybooks

```
- copy server-vars.yml and db-vars.yml into this directory
- create an inventory.ini that looks like:
```
[mysql-server]
MYSQL_IP_ADDRESS

[mongo-server]
MONGO_IP_ADDRESS

[edxapp-server]
localhost
```
- on the create an RSA keypair and add the public key to /home/USERNAME/.ssh/authorized_keys on each server
- run the playbook with
sudo ansible-playbook -i inventory.ini -u USERNAME multiserver_deploy.yml -e@./server-vars.yml -e@db-vars.yml &> ~/ansibleOutput.txt
