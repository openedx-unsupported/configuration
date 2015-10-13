FROM edxops/precise-common:v2
MAINTAINER e0d

USER docker
WORKDIR /edx/app/edx_ansible
ENV PATH /tmp/ansible/bin:/bin:/sbin:/usr/sbin:/usr/bin
#ENV ANSIBLE_LIBRARY /edx/app/edx_ansible/edx_ansible/playbooks/library
#ENV PYTHONPATH /tmp/ansible/lib:$PYTHON_PATH
ADD inventory /etc/ansible/hosts
WORKDIR /edx/app/edx_ansible/edx_ansible/playbooks/edx-east
RUN sudo git fetch --all
RUN sudo git checkout e0d/docker
RUN sudo ansible-playbook insights.yml -c local
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord -n --configuration /edx/app/supervisor/supervisord.conf"]
EXPOSE 22 443 80
