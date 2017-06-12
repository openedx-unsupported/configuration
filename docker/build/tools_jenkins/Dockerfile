FROM edxops/trusty-common:latest
MAINTAINER edxops

USER root
RUN apt-get update \
      && apt-get install -y apt-transport-https ca-certificates curl software-properties-common \
      && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
RUN apt-get update
RUN apt-get install -y docker-ce
RUN echo "jenkins ALL=NOPASSWD: ALL" >> /etc/sudoers

ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
COPY docker/build/tools_jenkins/ansible_overrides.yml /
RUN PYTHONUNBUFFERED=1 /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook -v jenkins_tools.yml -i '127.0.0.1,' -c local -e@/ansible_overrides.yml -vv -t 'install'

CMD /bin/su -l jenkins --shell=/bin/bash -c "/usr/bin/daemon -f --name=jenkins --inherit --env=JENKINS_HOME=/edx/var/jenkins --output=/var/log/jenkins/jenkins.log --pidfile=/var/run/jenkins/jenkins.pid -- /usr/bin/java  -jar /usr/share/jenkins/jenkins.war --webroot=/var/cache/jenkins/war --httpPort=8080 --ajp13Port=-1"
