FROM edxops/precise-common:v2
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
RUN sudo ansible-playbook forum.yml -i '127.0.0.1,' -c local -t "install:base,install:configuration,application-requirements,install:code" -e@/ansible_overrides.yml
WORKDIR /edx/app
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
EXPOSE 4567