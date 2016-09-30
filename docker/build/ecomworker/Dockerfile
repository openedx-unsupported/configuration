# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/ecomworker/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

FROM edxops/trusty-common:latest
MAINTAINER edxops

ENV ECOMMERCE_WORKER_VERSION=master
ENV REPO_OWNER=edx

ADD . /edx/app/edx_ansible/edx_ansible

WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

COPY docker/build/ecomworker/ansible_overrides.yml /
RUN sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook ecomworker.yml \
    -c local -i '127.0.0.1,' \
    -t 'install' \
    --extra-vars="@/ansible_overrides.yml" \
    --extra-vars="ECOMMERCE_WORKER_VERSION=$ECOMMERCE_WORKER_VERSION" \
    --extra-vars="COMMON_GIT_PATH=$REPO_OWNER"

USER root 
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
