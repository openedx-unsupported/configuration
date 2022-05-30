FROM edxops/xenial-common:latest
LABEL maintainer="edxops"

ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

# Role is currently untagged
RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook elasticsearch.yml -c local \
   -i '127.0.0.1,'

WORKDIR /etc/elasticsearch
CMD service elasticsearch start && sleep 5 && tail -f /edx/var/log/elasticsearch/elasticsearch.log
EXPOSE 9200 9300
