# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/discovery/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

FROM edxops/xenial-common:latest
MAINTAINER edxops
USER root
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]

ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

COPY docker/build/discovery/ansible_overrides.yml /
COPY docker/build/devstack/ansible_overrides.yml /devstack/ansible_overrides.yml

RUN sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook discovery.yml \
    -c local -i '127.0.0.1,' \
    -t 'install,assets,devstack' \
    --extra-vars="@/ansible_overrides.yml" \
    --extra-vars="@/devstack/ansible_overrides.yml"

EXPOSE 18381
