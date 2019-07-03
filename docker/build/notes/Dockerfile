# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/notes/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

ARG BASE_IMAGE_TAG=latest
FROM edxops/xenial-common:${BASE_IMAGE_TAG}
LABEL maintainer="edxops"

ARG OPENEDX_RELEASE=master
ENV OPENEDX_RELEASE=${OPENEDX_RELEASE}
ENV NOTES_VERSION=${OPENEDX_RELEASE}
ENV REPO_OWNER=edx

ADD . /edx/app/edx_ansible/edx_ansible

WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

COPY docker/build/notes/ansible_overrides.yml /
RUN sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook notes.yml \
    -c local -i '127.0.0.1,' \
    -t 'install,assets,devstack:install' \
    --extra-vars="@/ansible_overrides.yml" \
    --extra-vars="EDX_NOTES_API_VERSION=$NOTES_VERSION" \
    --extra-vars="COMMON_GIT_PATH=$REPO_OWNER"

USER root
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
