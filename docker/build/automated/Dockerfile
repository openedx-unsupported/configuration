FROM edxops/xenial-common:latest
LABEL maintainer="edxops"

ADD . /edx/app/edx_ansible/edx_ansible
COPY docker/build/automated/ansible_overrides.yml /
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook -vvvv automated.yml \
    -i '127.0.0.1,' -c local \
    -e@/ansible_overrides.yml
WORKDIR /edx/app
