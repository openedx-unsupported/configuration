# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/jenkins_build/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

ARG BASE_IMAGE_TAG=latest
FROM edxops/xenial-common:${BASE_IMAGE_TAG}
LABEL maintainer="edxops"

USER root
RUN apt-get update

ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
COPY docker/build/jenkins_build/ansible_overrides.yml /
RUN PYTHONUNBUFFERED=1 /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook \
    -v jenkins_build.yml \
    -i '127.0.0.1,' \
    -c local \
    -e@/ansible_overrides.yml \
    -t 'install' \
    -vv

CMD /bin/su -l jenkins --shell=/bin/bash -c "/usr/bin/daemon -f --name=jenkins --inherit --env=JENKINS_HOME=/edx/var/jenkins --output=/var/log/jenkins/jenkins.log --pidfile=/var/run/jenkins/jenkins.pid -- /usr/bin/java  -jar /usr/share/jenkins/jenkins.war --webroot=/var/cache/jenkins/war --httpPort=8080 --ajp13Port=-1"
