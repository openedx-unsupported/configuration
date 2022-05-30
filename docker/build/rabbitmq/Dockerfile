FROM edxops/xenial-common:latest
LABEL maintainer="edxops"

ADD . /edx/app/edx_ansible/edx_ansible
COPY docker/build/rabbitmq/ansible_overrides.yml /
COPY docker/build/rabbitmq/run_rabbitmq.sh /
RUN chmod +x /run_rabbitmq.sh

WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook rabbitmq.yml \
    -i '127.0.0.1,' -c local \
    -t 'install,manage:app-users' \
    -e@/ansible_overrides.yml

WORKDIR /edx/app
EXPOSE 15672 5672
CMD ["/run_rabbitmq.sh"]

