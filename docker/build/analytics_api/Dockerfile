FROM edxops/xenial-common:latest
MAINTAINER edxops

ARG ANALYTICS_API_VERSION=master
ENV PYTHONUNBUFFERED=1

ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook analytics_api.yml \
    -i '127.0.0.1,' -c local \
    -t "install:base,install:system-requirements,install:configuration,install:app-requirements,install:code,devstack" \
    -e "ANALYTICS_API_VERSION=$ANALYTICS_API_VERSION" \
    -e "analytics_api_gunicorn_host=0.0.0.0"

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/docker-command.sh"]
EXPOSE 8100
