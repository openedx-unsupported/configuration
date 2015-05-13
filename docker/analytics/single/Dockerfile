
FROM edxops/precise_basis:latest
MAINTAINER mulby

WORKDIR /edx/app/edx_ansible/edx_ansible
RUN git fetch origin gabe/analytics-docker && git checkout FETCH_HEAD .

WORKDIR /edx/app/edx_ansible
ENV PATH /edx/app/edx_ansible/venvs/edx_ansible/bin:/bin:/sbin:/usr/sbin:/usr/bin
ENV PYTHONUNBUFFERED 1
WORKDIR /edx/app/edx_ansible/edx_ansible/playbooks/edx-east
RUN apt-get update
RUN apt-get install ca-certificates
RUN ansible-playbook -c local analytics_single.yml

EXPOSE 22
USER hadoop
CMD ["/home/hadoop/run-all.sh"]
