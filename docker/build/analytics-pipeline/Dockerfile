# To build this Dockerfile:
#
# From the root of configuration:
#
# docker build -f docker/build/analytics-pipeline/Dockerfile .
#
# This allows the dockerfile to update /edx/app/edx_ansible/edx_ansible
# with the currently checked-out configuration repo.

FROM edxops/precise-common:latest
MAINTAINER edxops

ENV ANALYTICS_PIPELINE_VERSION=master
ENV REPO_OWNER=edx

ADD . /edx/app/edx_ansible/edx_ansible

WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

COPY docker/build/analytics-pipeline/ansible_overrides.yml /
RUN sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook analytics_pipeline.yml \
    -c local -i '127.0.0.1,' \
    -t 'install,devstack:install' \
    --extra-vars="@/ansible_overrides.yml" \
    --extra-vars="ANALYTICS_PIPELINE_VERSION=$ANALYTICS_PIPELINE_VERSION" \
    --extra-vars="COMMON_GIT_PATH=$REPO_OWNER"

USER root
CMD ["/edx/app/analytics_pipeline/devstack.sh"]

VOLUME ["/edx/app/analytics_pipeline/analytics_pipeline", "/data"]

# Hdfs ports
EXPOSE 50010 50020 50070 50075 50090
# Mapred ports
EXPOSE 19888
#Yarn ports
EXPOSE 8030 8031 8032 8033 8040 8042 8088
