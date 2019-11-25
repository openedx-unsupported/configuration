# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/jenkins_worker/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

# Run the edxapp play with custom ansible overrides
ARG BASE_IMAGE_TAG=latest
FROM edxops/xenial-common:${BASE_IMAGE_TAG}
LABEL maintainer="edxops"
USER root

ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

COPY docker/build/jenkins_worker/ansible_overrides.yml /jenkins_worker/ansible_overrides.yml
COPY docker/devstack_common_ansible_overrides.yml /devstack/ansible_overrides.yml

ARG OPENEDX_RELEASE=master
ENV OPENEDX_RELEASE=${OPENEDX_RELEASE}
RUN sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook edxapp.yml \
    -c local -i '127.0.0.1,' \
    -t 'install,assets,devstack' \
    --extra-vars="edx_platform_version=${OPENEDX_RELEASE}" \
    --extra-vars="@/jenkins_worker/ansible_overrides.yml" \
    --extra-vars="@/devstack/ansible_overrides.yml" \
    && rm -rf /edx/app/edxapp/.cache /edx/app/edxapp/edx-platform

# Add sshd to enable jenkins master to ssh into containers
RUN apt-get update \
  && apt-get install -y openssh-server \
  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ARG JENKINS_WORKER_KEY_URL=https://files.edx.org/testeng/jenkins.keys
RUN mkdir /var/run/sshd \
  && curl ${JENKINS_WORKER_KEY_URL} --create-dirs -o /edx/app/edxapp/.ssh/authorized_keys

CMD ["/usr/sbin/sshd", "-D"]
EXPOSE 22
