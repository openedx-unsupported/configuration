FROM edxops/xenial-common:latest
LABEL maintainer="edxops"

USER root
ADD . /edx/app/edx_ansible/edx_ansible
COPY docker/build/nginx/ansible_overrides.yml /
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays

RUN /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook nginx.yml -c local \
   -i '127.0.0.1,' \
   -e@roles/edxapp/defaults/main.yml \
   -e@roles/xqueue/defaults/main.yml \
   -e@roles/certs/defaults/main.yml \
   -e@roles/forum/defaults/main.yml

RUN echo "\ndaemon off;" >> /etc/nginx/nginx.conf
WORKDIR /etc/nginx
CMD ["/usr/sbin/nginx"]
EXPOSE 18000 48000 18010 48010 18020
