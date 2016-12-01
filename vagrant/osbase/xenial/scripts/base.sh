#!/bin/bash

apt-get update && \
apt-get upgrade -y && \
apt-get install -y build-essential \
                   linux-headers-virtual-lts-xenial \
                   linux-image-extra-virtual-lts-xenial \
                   curl \
                   wget \
                   cifs-utils \
                   acl

sed -i -e 's/noatime,/noatime,acl,/g' /etc/fstab

echo %vagrant ALL=NOPASSWD:ALL > /etc/sudoers.d/vagrant
chmod 0440 /etc/sudoers.d/vagrant

echo "UseDNS no" >> /etc/ssh/sshd_config

echo "fs.inotify.max_user_watches = 524288" >> /etc/sysctl.conf
echo "vm.swappiness = 10" >> /etc/sysctl.conf
