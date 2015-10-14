FROM edxoperations/precise-common:v2
MAINTAINER edxops

ENV CONFIG_BRANCH hack2015/gabe/analytics-hadoop

USER docker
WORKDIR /edx/app/edx_ansible/edx_ansible
RUN sudo git fetch --all
RUN sudo git checkout $CONFIG_BRANCH
RUN sudo git reset --hard origin/$CONFIG_BRANCH
RUN sudo git pull
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
RUN sudo ansible-playbook analytics_pipeline.yml -c local
USER root
CMD ["/edx/bin/analytics-pipeline-start.sh"]
