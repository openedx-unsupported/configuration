FROM ubuntu:trusty
MAINTAINER edxops 

RUN apt-get update
RUN apt-get -y install sudo
RUN useradd docker && echo "docker:docker" | chpasswd
RUN echo "docker ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
RUN mkdir -p /home/docker && chown -R docker:docker /home/docker
RUN apt-get install -y python2.7 python2.7-dev python-pip python-apt python-yaml python-jinja2 git
USER docker

# bootstrap
RUN sudo git clone --recursive https://github.com/edx/ansible /tmp/ansible
WORKDIR /tmp/ansible
ENV PATH /tmp/ansible/bin:/bin:/sbin:/usr/sbin:/usr/bin

# Install the configuration repository to install 
# edx-ansible role
RUN sudo git clone http://github.com/edx/configuration.git /tmp/configuration
ADD inventory /etc/ansible/hosts
WORKDIR /tmp/configuration
RUN sudo git checkout hack2015/docker
RUN sudo pip install -r pre-requirements.txt
RUN sudo pip install -r requirements.txt
WORKDIR /tmp/configuration/playbooks/edx-east
RUN sudo /tmp/ansible/bin/ansible-playbook edx_ansible.yml -c local -e "configuration_version=hack2015/docker"

# cleanup
RUN sudo rm -rf /tmp/ansible
RUN sudo rm -rf /tmp/configuration
