#!/bin/bash
set -e

# run forum playbook to setup config files
cd /edx/app/edx_ansible/edx_ansible/docker/plays

# Set ssl_verify to false for the mongoid configuration
sed -i '/ssl:.*/a \ \ \ \ ssl_verify: false' /edx/app/forum/cs_comments_service/config/mongoid.yml

if [[ -z "$RELEASE_NAME" ]]; then
    /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook \
        forum.yml \
        -i '127.0.0.1,' -c local \
        -e@/edx/etc/edxapp/ansible_overrides.yml \
        -e@/edx/app/edx_ansible/edx_ansible/docker/build/forum/vars/run.yml \
        -t "install:base,migrate"
else
    /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook \
        forum.yml \
        -i '127.0.0.1,' -c local \
        -e@/edx/etc/edxapp/ansible_overrides.yml \
        -e@/edx/app/edx_ansible/edx_ansible/docker/build/forum/vars/run.yml \
        -e@/edx/app/edx_ansible/edx_ansible/docker/build/forum/vars/k8s.yml \
        --extra-vars release_name=${RELEASE_NAME} \
        -t "install:base,migrate"
fi

exec "$@"
