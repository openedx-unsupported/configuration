FROM edxops/precise-common:v1
MAINTAINER e0d

USER docker
WORKDIR /edx/app/edx_ansible
ADD inventory /etc/ansible/hosts
WORKDIR /edx/app/edx_ansible/edx_ansible/playbooks/edx-east
RUN sudo git checkout e0d/docker-latest
RUN sudo git reset --hard origin/e0d/docker-latest
RUN sudo git pull
RUN sudo ansible-playbook elasticsearch-docker.yml -c local
USER root
WORKDIR /etc/elasticsearch
CMD ["/usr/share/elasticsearch/bin/elasticsearch"]
EXPOSE 9200 9300
