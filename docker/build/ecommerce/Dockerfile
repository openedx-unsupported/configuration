# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/ecommerce/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

FROM edxops/xenial-common:latest
MAINTAINER edxops

ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

RUN apt-get update

ENV ECOMMERCE_VERSION=master
ENV REPO_OWNER=edx

COPY docker/build/ecommerce/ansible_overrides.yml /

# NOTE: We are NOT compiling static assets due to the fact that database access is required to do so,
# and we do not have a database when building Docker images.
RUN sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook ecommerce.yml \
    -c local -i '127.0.0.1,' \
    -t 'install,devstack:install' \
    --extra-vars="@/ansible_overrides.yml" \
    --extra-vars="ECOMMERCE_VERSION=$ECOMMERCE_VERSION" \
    --extra-vars="COMMON_GIT_PATH=$REPO_OWNER"

USER root
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
EXPOSE 18130
