FROM edxops/xenial-common:latest
MAINTAINER edxops

USER root
ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook edx-monitoring.yml -c local \
   -i '127.0.0.1,'
