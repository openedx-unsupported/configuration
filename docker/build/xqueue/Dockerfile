# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/xqueue/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

ARG BASE_IMAGE_TAG=latest
FROM edxops/focal-common:${BASE_IMAGE_TAG}
LABEL maintainer="edxops"
ENTRYPOINT ["/edx/app/xqueue/devstack.sh"]
CMD ["start"]

USER root
RUN apt-get update
ADD . /edx/app/edx_ansible/edx_ansible
COPY docker/build/xqueue/ansible_overrides.yml /
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

ARG OPENEDX_RELEASE=master
ENV OPENEDX_RELEASE=${OPENEDX_RELEASE}
RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook xqueue.yml \
    -i '127.0.0.1,' \
    -c local \
    -t "install:base,install:system-requirements,install:configuration,install:app-requirements,install:code,devstack" \
    --extra-vars="XQUEUE_VERSION=${OPENEDX_RELEASE}" \
    --extra-vars="@/ansible_overrides.yml"

EXPOSE 18040
