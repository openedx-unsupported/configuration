FROM edxops/xenial-common:latest
LABEL maintainer="edxops"

USER root
RUN apt-get update

ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
COPY docker/build/jenkins_analytics/ansible_overrides.yml /
RUN PYTHONUNBUFFERED=1 /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook -v jenkins_analytics.yml -i '127.0.0.1,' -c local -e@/ansible_overrides.yml
