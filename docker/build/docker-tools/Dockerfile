# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/docker-tools/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

FROM edxops/xenial-common:latest
LABEL maintainer="edxops"

ENV REPO_OWNER=edx

ADD . /edx/app/edx_ansible/edx_ansible

WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

COPY docker/build/docker-tools/ansible_overrides.yml /
RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook docker-tools.yml \
    -c local -i '127.0.0.1,' \
    -t 'install'
RUN which docker
RUN which docker-compose
