FROM edxops/precise-common:latest
MAINTAINER edxops

RUN apt-get update

ADD . /edx/app/edx_ansible/edx_ansible
COPY docker/build/ecommerce/ansible_overrides.yml /
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

COPY docker/build/ecommerce/ansible_overrides.yml /
RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook ecommerce.yml -i '127.0.0.1,' -c local -t "install:base,install:system-requirements,install:configuration,install:app-requirements,install:code" -e@/ansible_overrides.yml
COPY docker/build/xqueue/docker-run.sh /
ENTRYPOINT ["/docker-run.sh"]
EXPOSE 8130
