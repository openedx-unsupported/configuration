FROM edxops/precise-common:v2
MAINTAINER edxops

USER docker
WORKDIR /edx/app/edx_ansible/edx_ansible/docker/plays
RUN sudo ansible-playbook forum.yml -c local
USER root 
CMD ["/edx/app/supervisor/venvs/supervisor/bin/supervisord", "-n", "--configuration", "/edx/app/supervisor/supervisord.conf"]
#ENTRYPOINT ["/bin/bash"]
EXPOSE 18080
