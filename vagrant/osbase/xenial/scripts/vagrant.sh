#!/bin/bash

mkdir -p /home/vagrant/.ssh
wget --no-check-certificate \
    'https://gist.githubusercontent.com/vadviktor/5cb616f164aa2e4f266a/raw/b0c22c8d34d5a3e7a1e596c4e2f55bcd7111951f/vagrant_rsa.pub' \
    -O /home/vagrant/.ssh/authorized_keys
chown -R vagrant /home/vagrant/.ssh
chmod -R go-rwsx /home/vagrant/.ssh
