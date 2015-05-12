#
# Dockerfile for create basis-precise image
#
# docker build --tag edxops/precice_basis:v1 .
#
# If it builds to completion
#
# docker run -i -n  edxops/precice_basis:v1 /bin/bash
# 

FROM ubuntu:precise
MAINTAINER mulby

RUN apt-get update
RUN apt-get install -y sudo python2.7 python2.7-dev python-pip python-apt python-yaml python-jinja2 git openssh-server

# download tools
RUN git clone http://github.com/edx/configuration.git /tmp/configuration

# setup configuration
WORKDIR /tmp/configuration
RUN pip install -U -r pre-requirements.txt
RUN pip install -r requirements.txt

# write ansible inventory
RUN mkdir /etc/ansible && echo '[local]\nlocalhost' > /etc/ansible/hosts

# run basic configuration
WORKDIR /tmp/configuration/playbooks/edx-east
ENV PYTHONUNBUFFERED 1
RUN ansible-playbook edx_ansible.yml -c local

# clean up tools
RUN rm -rf /tmp/configuration

WORKDIR /edx/app
