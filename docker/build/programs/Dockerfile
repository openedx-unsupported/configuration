# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/programs/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

FROM edxops/xenial-common:latest
MAINTAINER edxops

ENV PROGRAMS_VERSION=master
ENV REPO_OWNER=edx

ADD . /edx/app/edx_ansible/edx_ansible

WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

COPY docker/build/programs/ansible_overrides.yml /
RUN sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook programs.yml \
    -c local -i '127.0.0.1,' \
    -t 'install,assets' \
    --extra-vars="@/ansible_overrides.yml" \
    --extra-vars="PROGRAMS_VERSION=$PROGRAMS_VERSION" \
    --extra-vars="COMMON_GIT_PATH=$REPO_OWNER"

USER root 
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
