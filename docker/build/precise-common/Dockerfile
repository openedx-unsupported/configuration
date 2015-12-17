FROM ubuntu:precise 
MAINTAINER edxops 
ENV ANSIBLE_REPO="https://github.com/edx/ansible"
ENV CONFIGURATION_REPO="https://github.com/edx/configuration.git"
ENV CONFIGURATION_VERSION="master"

ADD util/install/ansible-bootstrap.sh /tmp/ansible-bootstrap.sh
RUN chmod +x /tmp/ansible-bootstrap.sh
RUN /tmp/ansible-bootstrap.sh
