FROM ubuntu:bionic

# Set the github runner version
ARG RUNNER_VERSION="2.273.0"

ENV GITHUB_ORGANIZATION=""
ENV GITHUB_ACCESS_TOKEN=""

# Update and install necessary packages
RUN apt-get update && apt-get install -y curl iputils-ping jq software-properties-common build-essential libssl-dev libffi-dev python3 python3-venv python3-dev

# Add a github action runner user
RUN useradd -m actions-runner

# cd into the user directory, download and unzip the github actions runner
RUN cd /home/actions-runner && mkdir actions-runner && cd actions-runner \
    && curl -O -L https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz \
    && tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz \
    && ./bin/installdependencies.sh \
    && chown -R actions-runner ~actions-runner \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install sudo to execute commands with root privileges
RUN apt-get update && apt-get install -y sudo

# Install packages needed for Docker installation
RUN apt-get update && apt-get install -y apt-transport-https gnupg-agent

# Add Docker's GPG key and repository
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable"

# Install Docker - for Docker CI running by github action runner
RUN apt-get update && apt-get install -y docker-ce

# Add the github actions-runner user to the docker group to allow the github action runner user to run docker commands.
# See: https://docs.docker.com/engine/installation/linux/ubuntulinux/
RUN usermod -aG docker actions-runner

# copy over the actions-runner.sh script
ADD docker/build/github-actions-runner/actions-runner.sh /actions-runner.sh

# make the script executable
RUN chmod +x actions-runner.sh

#set the user to "actions-runner" so all subsequent commands are run as the actions-runner user
USER actions-runner

# set the entrypoint to the actions-runner.sh script
ENTRYPOINT ["./actions-runner.sh"]
