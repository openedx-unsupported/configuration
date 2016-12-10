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

ARG ANALYTICS_PIPELINE_VERSION=master
ENV PYTHONUNBUFFERED=1

ADD . /edx/app/edx_ansible/edx_ansible
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook analytics_pipeline.yml \
    -c local -i '127.0.0.1,' \
    -e "ANALYTICS_PIPELINE_VERSION=$ANALYTICS_PIPELINE_VERSION"

USER hadoop
WORKDIR /edx/app/analytics_pipeline/analytics_pipeline/

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/bin/echo", "OK"]
