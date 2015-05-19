
FROM ubuntu:precise
MAINTAINER mulby

RUN apt-get update
RUN apt-get install -y sudo apt-utils net-tools python2.7 python2.7-dev python-pip python-apt python-yaml python-jinja2 git openssh-server

# download tools
RUN git clone --branch gabe/analytics-docker http://github.com/edx/configuration.git /tmp/configuration

# setup configuration
WORKDIR /tmp/configuration
RUN pip install -U -r pre-requirements.txt
RUN pip install -r requirements.txt

# write ansible inventory
RUN mkdir /etc/ansible && echo '[local]\nlocalhost' > /etc/ansible/hosts

# run basic configuration
WORKDIR /tmp/configuration/playbooks/edx-east
ENV PYTHONUNBUFFERED 1
RUN ansible-playbook -c local analytics_single.yml

EXPOSE 22
USER hadoop
CMD ["/home/hadoop/run-all.sh"]
