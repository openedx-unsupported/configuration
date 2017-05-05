#!/bin/bash

apt-get update
apt-get upgrade -y
apt-get install -y \
    build-essential \
    linux-headers-virtual-lts-xenial \
    linux-image-extra-virtual-lts-xenial \
    curl \
    wget \
    moreutils \
    vim

echo %vagrant ALL=NOPASSWD:ALL > /etc/sudoers.d/vagrant
chmod 0440 /etc/sudoers.d/vagrant

echo "UseDNS no" >> /etc/ssh/sshd_config

echo "vm.swappiness = 10" >> /etc/sysctl.conf
