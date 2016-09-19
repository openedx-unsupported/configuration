FROM edxops/trusty-common:v3
MAINTAINER edxops

ADD . /edx/app/edx_ansible/edx_ansible
COPY docker/build/xqwatcher/ansible_overrides.yml /
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook xqwatcher.yml \
    -i '127.0.0.1,' -c local \
    -t "install:base,install:configuration,install:system-requirements,install:app-requirements,install:code" \
    -e@/ansible_overrides.yml
WORKDIR /edx/app
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
