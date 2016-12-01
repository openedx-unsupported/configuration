#!/bin/bash

# enable memory and swap cgroup
sed -i 's/GRUB_CMDLINE_LINUX=""/GRUB_CMDLINE_LINUX="cgroup_enable=memory swapaccount=1"/g' /etc/default/grub
/usr/sbin/update-grub

# install mandatory packages
apt-get update && \
apt-get install -y apt-transport-https \
                   ca-certificates
apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
echo 'deb https://apt.dockerproject.org/repo ubuntu-xenial main' > /etc/apt/sources.list.d/docker.list
apt-get update && \
apt-get purge lxc-docker && \
apt-get install -y docker-engine \
                   apparmor

# https://docs.docker.com/engine/admin/systemd/#custom-docker-daemon-options
# enable Google DNS servers, lock in the default bridge ip, open API on unsecured tcp/ip
mkdir -p /etc/systemd/system/docker.service.d
echo "[Service] \n\
ExecStart= \n\
ExecStart=/usr/bin/docker daemon -H fd:// --bip=172.17.42.1/16 --dns 8.8.8.8 --dns 8.8.4.4 -H tcp://0.0.0.0:4242" > /etc/systemd/system/docker.service.d/daemon.conf

# add docker group and add vagrant to it
groupadd docker
usermod -a -G docker vagrant
