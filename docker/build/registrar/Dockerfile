# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/registrar/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

ARG BASE_IMAGE_TAG=latest
FROM edxops/focal-common:${BASE_IMAGE_TAG}
LABEL maintainer="edxops"
USER root
ENTRYPOINT ["/edx/app/registrar/devstack.sh"]
CMD ["start"]

ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

COPY docker/build/registrar/ansible_overrides.yml /
COPY docker/devstack_common_ansible_overrides.yml /devstack/ansible_overrides.yml
COPY docker/build/registrar/registrar.yml /edx/etc/registrar.yml

ARG OPENEDX_RELEASE=master
ENV OPENEDX_RELEASE=${OPENEDX_RELEASE}
RUN sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook registrar.yml \
    -c local -i "127.0.0.1," \
    -t "install,assets,devstack" \
    --extra-vars="REGISTRAR_VERSION=${OPENEDX_RELEASE}" \
    --extra-vars="@/ansible_overrides.yml" \
    --extra-vars="@/devstack/ansible_overrides.yml"

EXPOSE 18734
