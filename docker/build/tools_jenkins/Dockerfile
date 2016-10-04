FROM edxops/precise-common:latest
MAINTAINER edxops

USER root
RUN apt-get update

ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
COPY docker/build/tools_jenkins/ansible_overrides.yml /
RUN PYTHONUNBUFFERED=1 /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook -v jenkins_tools.yml -i '127.0.0.1,' -c local -e@/ansible_overrides.yml -vv
