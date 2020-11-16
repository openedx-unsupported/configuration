#!/bin/bash
set -e

cd /edx/app/edx_ansible/edx_ansible/docker/plays

if [[ -z "$RELEASE_NAME" ]]; then
    /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook \
        nginx.yml \
        -i '127.0.0.1,' -c local \
        -e@roles/edxapp/defaults/main.yml \
        -e@roles/forum/defaults/main.yml \
        -e@/edx/app/edx_ansible/edx_ansible/docker/build/nginx/vars/run.yml \
        -e@/edx/etc/edxapp/ansible_overrides.yml \
        -t "install:base,install:configuration"
else
    /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook \
        nginx.yml \
        -i '127.0.0.1,' -c local \
        -e@roles/edxapp/defaults/main.yml \
        -e@roles/forum/defaults/main.yml \
        -e@/edx/app/edx_ansible/edx_ansible/docker/build/nginx/vars/run.yml \
        -e@/edx/app/edx_ansible/edx_ansible/docker/build/nginx/vars/k8s.yml \
        -e@/edx/etc/edxapp/ansible_overrides.yml \
        --extra-vars release_name=${RELEASE_NAME} \
        -t "install:base,install:configuration"
fi

# playbook starts nginx, but we don't want it to be running
service nginx stop

exec "$@"
