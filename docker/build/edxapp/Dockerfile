FROM edxops/precise-common
MAINTAINER edxops

ENV CONFIGURATION_REPO="https://github.com/edx/configuration.git"
ENV CONFIGURATION_VERSION="hack2015/docker"

USER docker

RUN sudo apt-get update

WORKDIR /edx/app/edx_ansible/edx_ansible
RUN sudo git fetch --all
RUN sudo git checkout ${CONFIGURATION_VERSION}
RUN sudo git reset --hard origin/${CONFIGURATION_VERSION}
RUN sudo git pull
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
COPY ansible_overrides.yml /

RUN sudo ansible-playbook edxapp.yml -c local -e "EDXAPP_PYTHON_SANDBOX=false" -t "install:base,install:configuration,install:application-requirements,install:code" -e@/ansible_overrides.yml
USER root
WORKDIR /edx/app
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
EXPOSE 8000 8010
