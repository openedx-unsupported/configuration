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

ENV REPO_OWNER=edx

ADD . /edx/app/edx_ansible/edx_ansible

WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

RUN sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook luigid.yml \
    -c local -i '127.0.0.1,' \
    -t 'install' \
    --extra-vars="COMMON_GIT_PATH=$REPO_OWNER"

USER luigid
EXPOSE 9100
CMD ["/edx/app/luigid/venvs/luigid/bin/luigid", "--address=0.0.0.0", "--port=9100", "--state-path=/var/tmp/luigi-state.pickle"]
