#!/usr/bin/env bash

# Kill the apt services holding a dpkg lock, so that the ansible-bootstrap
# script can run without conflicts.

# NOTE: this is a temporary fix. Instead, we should be doing what devops does,
# and first run the security+common roles on a vanilla AMI, which will disable
# unattended-updates and set up users. Then we can feel free to run the
# ansible bootstrap without any problems.

set -xe

if grep -q 'Xenial Xerus' /etc/os-release; then
    systemctl stop apt-daily.service
    systemctl kill --kill-who=all apt-daily.service
    # Our jenkins job for building AMIs will timeout, even if the lock is
    # never released.
    while lsof |grep -q /var/lib/dpkg/lock; do
        echo "Waiting for apt to release the dpkg lock..."
        sleep 5
    done
fi

