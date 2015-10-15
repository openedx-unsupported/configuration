FROM edxops/precise-common:v2
MAINTAINER edxops

USER docker

RUN sudo apt-get update

WORKDIR /edx/app/edx_ansible/edx_ansible
RUN sudo git fetch --all
RUN sudo git checkout hack2015/docker
RUN sudo git reset --hard hack2015/docker
RUN sudo git pull
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

RUN sudo ansible-playbook forum.yml -c local -t 'install:base,install:configuration,install:code' -e '{"FORUM_MONGO_HOSTS":["forums-mongo.local.edx.org"]}' -e FORUM_ELASTICSEARCH_HOST='forums-elasticsearch.local.edx.org'
USER root 
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
#ENTRYPOINT ["/bin/bash"]
EXPOSE 18080
