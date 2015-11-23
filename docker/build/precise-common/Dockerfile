FROM ubuntu:precise 
MAINTAINER edxops 
ENV ANSIBLE_REPO="https://github.com/edx/ansible"
ENV CONFIGURATION_REPO="https://github.com/edx/configuration.git"
ENV CONFIGURATION_VERSION="hack2015/docker"

# system bootstrap
RUN apt-get update
RUN apt-get -y install sudo
RUN useradd docker && echo "docker:docker" | chpasswd
RUN echo "docker ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
RUN mkdir -p /home/docker && chown -R docker:docker /home/docker
RUN apt-get install -y python2.7 python2.7-dev python-pip python-apt python-yaml python-jinja2 git
USER docker

# ansible bootstrap
RUN sudo git clone --recursive ${ANSIBLE_REPO} /tmp/ansible
WORKDIR /tmp/ansible
ENV PATH /tmp/ansible/bin:/bin:/sbin:/usr/sbin:/usr/bin

# Install the configuration repository to install 
# edx-ansible role
RUN sudo git clone ${CONFIGURATION_REPO} /tmp/configuration
WORKDIR /tmp/configuration
RUN sudo git checkout ${CONFIGURATION_VERSION}
RUN sudo pip install -r pre-requirements.txt
RUN sudo pip install -r requirements.txt
WORKDIR /tmp/configuration/playbooks/edx-east
RUN sudo /tmp/ansible/bin/ansible-playbook edx_ansible.yml -i '127.0.0.1,' -c local -e "configuration_version=${CONFIGURATION_VERSION}"
WORKDIR /edx/app/edx_ansible
# cleanup
RUN sudo rm -rf /tmp/ansible
RUN sudo rm -rf /tmp/configuration
