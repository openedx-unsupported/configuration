FROM edxops/precise-common:v1
MAINTAINER edxops

USER docker
WORKDIR /edx/app/edx_ansible/edx_ansible
RUN sudo git fetch --all
RUN sudo git checkout e0d/docker-latest
RUN sudo git reset --hard origin/e0d/docker-latest
RUN sudo git pull
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
RUN sudo ansible-playbook nginx.yml -c local \
   -e@roles/edxapp/defaults/main.yml \
   -e@roles/xqueue/defaults/main.yml \
   -e@roles/ora/defaults/main.yml \
   -e@roles/certs/defaults/main.yml

USER root
RUN echo "\ndaemon off;" >> /etc/nginx/nginx.conf
WORKDIR /etc/nginx
CMD ["/usr/sbin/nginx"]
EXPOSE 18000 48000 18010 48010 18020
