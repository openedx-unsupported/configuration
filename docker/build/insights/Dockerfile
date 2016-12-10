FROM edxops/xenial-common:latest
MAINTAINER edxops

ARG INSIGHTS_VERSION=master
ENV PYTHONUNBUFFERED=1

ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook insights.yml \
    -i '127.0.0.1,' -c local \
    -t "install:base,install:system-requirements,install:configuration,install:app-requirements,install:code,devstack:install" \
    -e "INSIGHTS_VERSION=$INSIGHTS_VERSION" \
    -e "insights_gunicorn_host=0.0.0.0"

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/docker-command.sh"]
EXPOSE 8110
