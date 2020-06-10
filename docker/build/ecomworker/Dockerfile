# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/ecomworker/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

ARG BASE_IMAGE_TAG=latest
FROM edxops/xenial-common:${BASE_IMAGE_TAG}
LABEL maintainer="edxops"

ADD . /edx/app/edx_ansible/edx_ansible

WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

COPY docker/build/ecomworker/ansible_overrides.yml /
COPY docker/build/ecomworker/ecomworker.yml /edx/etc/ecomworker.yml

ARG OPENEDX_RELEASE=master
ENV OPENEDX_RELEASE=${OPENEDX_RELEASE}
RUN sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook ecomworker.yml \
    -c local -i '127.0.0.1,' \
    -t "install:base,install:system-requirements,install:configuration,install:app-requirements,install:code" \
    --extra-vars="ECOMMERCE_WORKER_VERSION=${OPENEDX_RELEASE}" \
    --extra-vars="@/ansible_overrides.yml"

USER root
ENTRYPOINT ["/edx/app/ecomworker/devstack.sh"]
CMD ["start"]
