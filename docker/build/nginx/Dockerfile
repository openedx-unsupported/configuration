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
   -e@roles/certs/defaults/main.yml \
   -e "nginx_lms_gunicorn_hosts=lms.local.edx.org"
   -e "nginx_cms_gunicorn_hosts=cms.local.edx.org"
   -e "nginx_xserver_gunicorn_hosts=xserver.local.edx.org"
   -e "nginx_xqueue_gunicorn_hosts=xqueue.local.edx.org"
   -e "nginx_lms_preview_gunicorn_hosts=lms-preview.local.edx.org"
   -e "nginx_analytics_api_gunicorn_hosts=analytics-api.local.edx.org"
   -e "nginx_insights_gunicorn_hosts=insights.local.edx.org"
   -e "nginx_edx_notes_api_gunicorn_hosts=edx-notes.local.edx.org"
   -e "nginx_ecommerce_gunicorn_hosts=ecommerce.local.edx.org"
   -e "nginx_programs_gunicorn_hosts=programs.local.edx.org"

USER root
RUN echo "\ndaemon off;" >> /etc/nginx/nginx.conf
WORKDIR /etc/nginx
CMD ["/usr/sbin/nginx"]
EXPOSE 18000 48000 18010 48010 18020
