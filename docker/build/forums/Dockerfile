FROM edxops/precise-common:latest
MAINTAINER edxops

RUN apt-get update

WORKDIR /edx/app/edx_ansible/edx_ansible

WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
COPY docker/build/forums/ansible_overrides.yml /
RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook forum.yml -i '127.0.0.1,' -c local -t "install:base,install:configuration,application-requirements,install:code" -e@/ansible_overrides.yml
WORKDIR /edx/app
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
EXPOSE 4567