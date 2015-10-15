FROM edxops/precise-common
MAINTAINER edxops

USER docker
WORKDIR /edx/app/edx_ansible/edx_ansible
RUN sudo git fetch --all
RUN sudo git checkout e0d/diverse-virtualization-targets
RUN sudo git reset --hard e0d/diverse-virtualization-targets
RUN sudo git pull
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
ADD ansible.cfg /edx/app/edx_ansible/edx_ansible/docker/plays/ansible.cfg 
RUN sudo ansible-playbook edxapp.yml -c local -e "EDXAPP_PYTHON_SANDBOX=false" -t 'install:base'
RUN sudo ansible-playbook edxapp.yml -c local -e "EDXAPP_PYTHON_SANDBOX=false" -t 'install:code'
RUN sudo ansible-playbook edxapp.yml -c local -e "EDXAPP_PYTHON_SANDBOX=false" -t 'install:configuration'
USER root 
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
EXPOSE 18000 48000 18020 18010 48010 8010 8000 
