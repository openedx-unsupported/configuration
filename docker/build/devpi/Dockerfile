# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/devpi/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

ARG BASE_IMAGE_TAG=latest
FROM edxops/xenial-common:${BASE_IMAGE_TAG}
LABEL maintainer="edxops"

ARG ARG_DEVPI_SERVER_VERSION=4.4.0
ARG ARG_DEVPI_WEB_VERSION=3.2.2
ARG ARG_DEVPI_CLIENT_VERSION=4.0.0

ADD . /edx/app/edx_ansible/edx_ansible

WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

RUN apt-get update

COPY docker/devstack_common_ansible_overrides.yml /devstack/ansible_overrides.yml

RUN sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook devpi.yml \
    -c local -i '127.0.0.1,' \
    -t "install,devstack" \
    --extra-vars="@/devstack/ansible_overrides.yml" \
    --extra-vars="DEVPI_SERVER_VERSION=$ARG_DEVPI_SERVER_VERSION" \
    --extra-vars="DEVPI_WEB_VERSION=$ARG_DEVPI_WEB_VERSION" \
    --extra-vars="DEVPI_CLIENT_VERSION=$ARG_DEVPI_CLIENT_VERSION"

EXPOSE 3141
VOLUME /data

COPY docker/build/devpi/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

USER root
ENV HOME /data
WORKDIR /data

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["devpi"]
