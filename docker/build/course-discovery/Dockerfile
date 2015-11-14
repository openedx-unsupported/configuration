FROM edxops/trusty-common
MAINTAINER edxops

ARG config_hash=origin/master
ARG course_discovery_version=master
ARG repo_owner=edx

ENV ansible_playbook=/edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook

USER root
RUN apt-get -y install libmysqlclient-dev
RUN pip install MySQL-python

USER docker
WORKDIR /edx/app/edx_ansible/edx_ansible
ENV BRANCH=edx-course-discovery
RUN sudo git fetch --all && sudo git checkout $config_hash
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
ADD ansible.cfg /edx/app/edx_ansible/edx_ansible/docker/plays/ansible.cfg

# This is a dirty hack
#RUN sudo pip install MySQL-python

RUN sudo $ansible_playbook course_discovery.yml -c local -t 'install:base'
RUN sudo $ansible_playbook course_discovery.yml -c local -t 'install:code' \
    --extra-vars="COURSE_DISCOVERY_VERSION=$course_discovery_version" \
    --extra-vars="COMMON_GIT_PATH=$repo_owner"
RUN sudo $ansible_playbook course_discovery.yml -c local -t 'install:system-requirements'
RUN sudo $ansible_playbook course_discovery.yml -c local -t 'install:app-requirements'
RUN sudo $ansible_playbook course_discovery.yml -c local -t 'install:configuration' \
    --extra-vars="course_discovery_gunicorn_host=0.0.0.0"
RUN sudo $ansible_playbook course_discovery.yml -c local -t 'install:devstack'
USER root 
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
