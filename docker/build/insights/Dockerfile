FROM edxops/xenial-common:latest
MAINTAINER edxops

ADD . /edx/app/edx_ansible/edx_ansible
COPY docker/build/insights/ansible_overrides.yml /
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook insights.yml \
    -i '127.0.0.1,' -c local \
    -t "install:base,install:system-requirements,install:configuration,install:app-requirements,install:code" \
    -e@/ansible_overrides.yml
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
EXPOSE 8110 18110
