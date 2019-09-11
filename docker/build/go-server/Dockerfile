ARG BASE_IMAGE_TAG=latest
FROM edxops/xenial-common:${BASE_IMAGE_TAG}
LABEL maintainer="edxops"

ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /var/lib/go-server

COPY docker/build/go-server/ansible_overrides.yml /ansible_overrides.yml

ARG OPENEDX_RELEASE=master
ENV OPENEDX_RELEASE=${OPENEDX_RELEASE}

RUN sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook /edx/app/edx_ansible/edx_ansible/docker/plays/go-server.yml \
  -c local -i '127.0.0.1,' \
 -t 'install,assets,devstack' \
 --extra-vars="@/ansible_overrides.yml"

USER go
EXPOSE 8153 8154
