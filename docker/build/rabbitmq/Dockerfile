FROM edxops/precise-common:latest
MAINTAINER edxops

USER root
ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

# Role is currently untagged
RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook rabbitmq.yml -c local \
   -i '127.0.0.1,'

USER rabbitmq
# TBD what we want to run rabbit under
EXPOSE 15672 5672
