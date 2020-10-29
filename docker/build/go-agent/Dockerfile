# To run, use the command docker build . -f docker/build/go-agent/Dockerfile --tag edx-ops/go-agent:latest
# https://hub.docker.com/r/gocd/gocd-agent-ubuntu-16.04/
FROM gocd/gocd-agent-ubuntu-16.04:v17.10.0

LABEL version="0.02" \
      description="This custom go-agent docker file installs additional requirements for the edx pipeline"

# Set locale to UTF-8 which is not the default for go-agent Docker container
RUN apt-get update &&\
    apt-get install -y locales &&\
    locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# starting with 16.04 apt-get-repository is not installed in the base image, lets install it so we are ready
# http://lifeonubuntu.com/ubuntu-missing-add-apt-repository-command/
RUN apt-get update && apt-get install -y -q \
    software-properties-common \
    python-software-properties

# Install a modern git client
RUN add-apt-repository -y ppa:git-core/ppa && \
    apt-get update && \
    apt-get -y install git

# Configure ca-certificates for java
RUN /var/lib/dpkg/info/ca-certificates-java.postinst configure

# Define working directory.
WORKDIR /data

# Install Python and package mgmt tools.
RUN apt-get update && apt-get install -y -q \
    python \
    python-dev \
    python-distribute \
    python-pip \
    libmysqlclient-dev \
    python3-pip

# Install dependencies needed for Ansible 2.x
RUN apt-get update && apt-get install -y libffi-dev libssl-dev

# Install sudo to execute commands with root privileges
RUN apt-get install -y sudo

# Install packages needed for Docker installation
RUN apt-get update && apt-get install -y apt-transport-https gnupg-agent

# Add Docker's GPG key and repository
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable"

# Install Docker - for Docker container building by a go-agent.
RUN apt-get update && apt-get install -y docker-ce

# Add the go user to the docker group to allow the go user to run docker commands.
# See: https://docs.docker.com/engine/installation/linux/ubuntulinux/
RUN usermod -aG docker go

# Assign the go user root privlidges
RUN printf "\ngo      ALL=(ALL:ALL) NOPASSWD: /usr/bin/pip, /usr/local/bin/pip\n" >> /etc/sudoers
RUN printf "\ngo      ALL=(ALL:ALL) NOPASSWD: /usr/bin/pip3, /usr/local/bin/pip3\n" >> /etc/sudoers
RUN printf "\ngo      ALL=(ALL:ALL) NOPASSWD: /usr/bin/pip3.6, /usr/local/bin/pip3.6\n" >> /etc/sudoers

# Upgrade pip and setup tools. Needed for Ansible 2.x
RUN \
  pip3 install --upgrade pip==20.0.2 && \
  pip2 install --upgrade pip==20.0.2 && \
  #pip may have moved from /usr/bin/ to /usr/local/bin/. This clears bash's path cache.
  hash -r && \
  # upgrade setuptools early to avoid no distribution errors
  pip install --upgrade setuptools==44.1.0 && \
  pip3 install --upgrade setuptools==44.1.0

# Compile python 3.6 for Zappa, as zappa requires python 2.7 or 3.6.
# There is no bionic GOCD official image published to base off of, and there is no official 3.6 python package for ubuntu 14.04 or 16.04
# This will only be on your path as 'python3.6' it will not change the current 'python3' on your path to python 3.6
# This isnt a separate agent because deploys of this are likely quite rare.
# If we update the GOCD agent to use ubuntu > 14 we can just use the python3
# that is already installed for zappa deployments.
RUN apt-get update && apt-get install zlib1g-dev wget lsb-core -qy && cd /opt && wget https://www.python.org/ftp/python/3.6.7/Python-3.6.7.tgz && tar -xvf Python-3.6.7.tgz && cd /opt/Python-3.6.7 && ./configure --prefix=/usr && cd /opt/Python-3.6.7 && make && make commoninstall maninstall && rm -rf /opt/Python-3.6.7

# Install AWS command-line interface - for AWS operations in a go-agent task.
RUN pip install 'awscli>=1.11.58'

# Install pip on python3.6 to install asym-crypto-yaml which requires python >= 3.6
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.6 get-pip.py

# !!!!NOTICE!!!! ---- Runner of this pipeline take heed!! You must replace go_github_key.pem with the REAL key material
# that can checkout private github repositories used as pipeline materials. The key material here is faked and is only
# used to pass CI!
# setup the github identity
ADD docker/build/go-agent/files/go_github_key.pem /home/go/.ssh/id_rsa
RUN chmod 600 /home/go/.ssh/id_rsa && \
    chown go:go /home/go/.ssh/id_rsa

# setup the known_hosts
RUN touch /home/go/.ssh/known_hosts && \
    chmod 600 /home/go/.ssh/known_hosts && \
    chown go:go /home/go/.ssh/known_hosts && \
    ssh-keyscan -t rsa,dsa github.com > /home/go/.ssh/known_hosts
