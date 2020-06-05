# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/enterprise_catalog/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

ARG BASE_IMAGE_TAG=latest
FROM edxops/xenial-common:${BASE_IMAGE_TAG}
MAINTAINER edxops
USER root
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]

ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

COPY docker/build/enterprise_catalog/ansible_overrides.yml /
COPY docker/devstack_common_ansible_overrides.yml /devstack/ansible_overrides.yml
COPY docker/build/enterprise_catalog/enterprise_catalog.yml /edx/etc/enterprise_catalog.yml

ARG OPENEDX_RELEASE=master
ENV OPENEDX_RELEASE=${OPENEDX_RELEASE}
RUN sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook enterprise_catalog.yml \
    -c local -i "127.0.0.1," \
    -t "install,assets,devstack" \
    --extra-vars="ENTERPRISE_CATALOG_VERSION=${OPENEDX_RELEASE}" \
    --extra-vars="@/ansible_overrides.yml" \
    --extra-vars="@/devstack/ansible_overrides.yml"

EXPOSE 18160
