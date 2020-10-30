# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/analytics_api/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

ARG BASE_IMAGE_TAG=latest
FROM edxops/focal-common:${BASE_IMAGE_TAG}
LABEL maintainer="edxops"

RUN apt-get update

ADD . /edx/app/edx_ansible/edx_ansible
COPY docker/build/analytics_api/ansible_overrides.yml /
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

COPY docker/build/analytics_api/ansible_overrides.yml /
COPY docker/build/analytics_api/analytics_api.yml /edx/etc/analytics_api.yml

ARG OPENEDX_RELEASE=master
ENV OPENEDX_RELEASE=${OPENEDX_RELEASE}
RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook analytics_api.yml \
    -i '127.0.0.1,' \
    -c local \
    -t "install:base,install:system-requirements,install:configuration,install:app-requirements,install:code,devstack:install" \
    --extra-vars="ANALYTICS_API_VERSION=${OPENEDX_RELEASE}" \
    --extra-vars="@/ansible_overrides.yml"
WORKDIR /edx/app/
ENTRYPOINT ["/edx/app/analytics_api/devstack.sh"]
CMD ["start"]
EXPOSE 443 80
