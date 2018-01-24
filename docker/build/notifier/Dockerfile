FROM edxops/xenial-common:latest
MAINTAINER edxops

WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
ADD . /edx/app/edx_ansible/edx_ansible
COPY docker/build/notifier/ansible_overrides.yml /
RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook notifier.yml \
    -i '127.0.0.1,' -c local \
    -t 'install' \
    -e@/ansible_overrides.yml
WORKDIR /edx/app
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
