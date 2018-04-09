FROM edxops/xenial-common:latest
MAINTAINER edxops

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
