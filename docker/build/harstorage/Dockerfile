FROM edxops/precise-common
MAINTAINER edxops

USER root
RUN curl http://salilab.org/~ben/libselinux1_2.1.0-5.1ubuntu1_amd64.deb -o /tmp/libselinux1_2.1.0-5.1ubuntu1_amd64.deb
RUN dpkg -i /tmp/libselinux1_2.1.0-5.1ubuntu1_amd64.deb
RUN apt-get update
ADD . /edx/app/edx_ansible/edx_ansible
COPY docker/build/xqwatcher/ansible_overrides.yml /
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook harstorage.yml \
    -i '127.0.0.1,' -c local \
    -t "install:base,install:configuration,install:app-requirements,install:code" \    
    -e@/ansible_overrides.yml
WORKDIR /edx/app
#CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
