FROM edxops/trusty-common
MAINTAINER edxops

ARG config_hash=origin/master

USER docker
WORKDIR /edx/app/edx_ansible/edx_ansible
ENV BRANCH=edx-course-discovery
RUN sudo git fetch --all && sudo git checkout $config_hash
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
ADD ansible.cfg /edx/app/edx_ansible/edx_ansible/docker/plays/ansible.cfg 
RUN sudo ansible-playbook course_discovery.yml -c local -t 'install:base'
RUN sudo ansible-playbook course_discovery.yml -c local -t 'install:code'
RUN sudo ansible-playbook course_discovery.yml -c local -t 'install:system-requirements'
RUN sudo ansible-playbook course_discovery.yml -c local -t 'install:app-requirements'
RUN sudo ansible-playbook course_discovery.yml -c local -t 'install:configuration'
RUN sudo ansible-playbook course_discovery.yml -c local -t 'install:vhosts'
USER root 
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
